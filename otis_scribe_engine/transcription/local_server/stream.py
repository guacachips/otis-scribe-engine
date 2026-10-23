import json
import queue
import threading
import time
import traceback
import numpy as np
from websockets.exceptions import InvalidStatus
from websockets.sync.client import connect
from .local_server import DEFAULT_BASE_URL, DEFAULT_MODEL, LocalServerUnavailableError

SAMPLE_RATE = 16000
REALTIME_PATH = "/v1/audio/transcriptions/realtime"
# 4000 recorder blocks of 512 samples ≈ 2 minutes of audio the sender has not sent yet.
QUEUE_BLOCKS = 4000


class LocalServerLiveTranscriber:
    """Live transcription through a local otis-speech-server WebSocket (text arrives while audio is fed)."""

    def __init__(self, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL, transcription_delay_ms=480,
                 on_delta=None, on_error=None, on_final=None, chunk_ms=320, debug=False):
        """Initialize live transcriber. Callbacks run on the receiver thread and must not block.

        Args:
            base_url: otis-speech-server address (http://host:port)
            model: Server model id; it must be a streaming model (e.g., "voxtral-realtime-4bit")
            transcription_delay_ms: Server-side delay between audio and text (240-2400)
            on_delta: Callable(delta, text_so_far) for each new piece of text
            on_error: Callable(exc) when the session fails before its final text (server error or
                lost connection); exc is the RuntimeError that finish() will raise
            on_final: Callable(stop_reason) when the final text arrives; a stop_reason other than
                "end" ("eos", "max_duration") means the server ended the session on its own, so the
                caller should stop recording and call finish() for the result
            chunk_ms: Audio sent per WebSocket frame (a multiple of 80 ms matches the model's tokens)
            debug: Enable debug output (never prints transcribed text)
        """
        self.base_url = base_url.rstrip("/")
        self.ws_url = self.base_url.replace("http", "ws", 1) + REALTIME_PATH
        self.model = model
        self.transcription_delay_ms = transcription_delay_ms
        self.on_delta = on_delta
        self.on_error = on_error
        self.on_final = on_final
        self.chunk_samples = int(SAMPLE_RATE * chunk_ms / 1000)
        self.debug = debug

        self._queue = queue.Queue(maxsize=QUEUE_BLOCKS)
        self._ws = None
        self._sender = None
        self._receiver = None
        self._lock = threading.Lock()
        self._text = ""
        self._dropped_samples = 0
        self._end_requested = threading.Event()
        self._stopping = threading.Event()   # stop sending: cancel, final or failure
        self._done = threading.Event()       # final or failure received
        self._closed_locally = False   # cancel(), finish() or a finish() timeout closed the socket
        self._result = None
        self._error = None
        self._end_sent_at = None
        self._final_at = None

    @property
    def text(self):
        """Text received so far."""
        with self._lock:
            return self._text.strip()

    @property
    def dropped_seconds(self):
        """Audio dropped because the sender fell behind (the queue was full)."""
        return self._dropped_samples / SAMPLE_RATE

    def start(self):
        """Open the session. Returns without waiting for the model; feed() may start right away.

        Raises:
            LocalServerUnavailableError: the server is not reachable
            TimeoutError: the server accepted the connection but did not complete the handshake
            RuntimeError: the server refused the WebSocket (e.g. a server without live transcription)
        """
        if self._ws is not None:
            raise RuntimeError("start() was already called")
        try:
            # proxy=None: a proxy from the environment or macOS settings must never relay a local server.
            self._ws = connect(self.ws_url, open_timeout=5, max_size=1 << 20, proxy=None)
        except InvalidStatus as e:
            raise RuntimeError(
                f"otis-speech-server at {self.base_url} refused live transcription "
                f"(HTTP {e.response.status_code}); it may predate the realtime endpoint"
            ) from None
        except TimeoutError:
            raise TimeoutError(f"otis-speech-server at {self.base_url} did not open a WebSocket within 5s") from None
        except OSError as e:
            raise LocalServerUnavailableError(self.base_url) from e

        start_message = {
            "type": "start",
            "model": self.model,
            "transcription_delay_ms": self.transcription_delay_ms,
            "sample_rate": SAMPLE_RATE,
            "encoding": "pcm_s16le",
        }
        try:
            self._ws.send(json.dumps(start_message))
        except Exception as e:
            self._ws.close()
            self._ws = None
            raise LocalServerUnavailableError(self.base_url) from e

        if self.debug:
            print(f"Live transcription with otis-speech-server at {self.ws_url}, model: {self.model}")

        self._sender = threading.Thread(target=self._send_loop, name="otis-live-sender", daemon=True)
        self._receiver = threading.Thread(target=self._receive_loop, name="otis-live-receiver", daemon=True)
        self._receiver.start()
        self._sender.start()

    def feed(self, samples):
        """Queue float32 mono 16 kHz samples; never blocks (audio is dropped if the queue is full).

        The array must not be modified afterwards (AudioRecorder's on_audio passes a copy).
        """
        if self._end_requested.is_set() or self._stopping.is_set():
            return
        try:
            self._queue.put_nowait(samples)
        except queue.Full:
            if self._dropped_samples == 0:
                print("\nLive transcription is falling behind: dropping audio")
            self._dropped_samples += len(samples)

    def finish(self, timeout=60.0):
        """Send the remaining audio, end the session and wait for the final text.

        Returns:
            dict: {'text': str, 'transcription_time': float, 'model': str, 'stats': dict}
            transcription_time is the time from the end of the audio to the final text.

        Raises:
            RuntimeError: the session failed (server error or lost connection); the exception
                carries .code (server error code or None) and .partial_text
            TimeoutError: no final text within timeout seconds (also carries .partial_text)
        """
        if self._ws is None:
            raise RuntimeError("start() was not called")
        self._end_requested.set()
        if not self._done.wait(timeout):
            self._close()
            error = TimeoutError(f"otis-speech-server sent no final text within {timeout}s")
            error.partial_text = self.text
            raise error
        self._close()
        if self._error is not None:
            raise self._error

        transcription_time = self._final_at - self._end_sent_at if self._end_sent_at else 0.0
        if self.debug:
            stats = self._result["stats"]
            print(f"Live transcription finalized in {transcription_time:.2f}s "
                  f"(stop_reason={stats.get('stop_reason')}, audio_s={stats.get('audio_s')})")
        return {**self._result, 'transcription_time': float(transcription_time)}

    def cancel(self):
        """Drop the session without a final text (best effort; safe to call more than once)."""
        self._stopping.set()
        if self._ws is None:
            return
        if not self._done.is_set():
            try:
                self._ws.send(json.dumps({"type": "cancel"}))
            except Exception:
                pass
        self._close()

    def _close(self):
        self._closed_locally = True
        self._stopping.set()
        self._ws.close()
        # A callback may call finish() or cancel() from the receiver thread: never join yourself.
        for thread in (self._sender, self._receiver):
            if thread is not threading.current_thread():
                thread.join(timeout=5)

    def _send_loop(self):
        pending = []
        pending_samples = 0
        try:
            while not self._stopping.is_set():
                try:
                    block = self._queue.get(timeout=0.05)
                except queue.Empty:
                    if self._end_requested.is_set() and self._queue.empty():
                        if pending_samples:
                            self._ws.send(_to_pcm16(np.concatenate(pending)))
                        self._end_sent_at = time.time()
                        self._ws.send(json.dumps({"type": "end"}))
                        return
                    continue
                pending.append(block)
                pending_samples += len(block)
                # Exact chunk_samples frames keep the server's token boundaries independent of the recorder's block size.
                if pending_samples >= self.chunk_samples:
                    audio = np.concatenate(pending)
                    sendable = len(audio) - len(audio) % self.chunk_samples
                    for start in range(0, sendable, self.chunk_samples):
                        self._ws.send(_to_pcm16(audio[start:start + self.chunk_samples]))
                    pending = [audio[sendable:]]
                    pending_samples = len(pending[0])
        except Exception as e:
            # A closed connection also ends the receiver, which reports it; this covers other failures.
            if not self._stopping.is_set():
                self._fail(None, f"sending audio failed: {e or type(e).__name__}")

    def _receive_loop(self):
        try:
            for message in self._ws:
                if isinstance(message, bytes):
                    continue
                event = json.loads(message)
                kind = event.get("type")
                if kind == "ready":
                    if self.debug:
                        print(f"Live session ready: {event.get('session_id')} "
                              f"({event.get('compute_dtype')}, delay {event.get('transcription_delay_ms')} ms)")
                elif kind == "delta":
                    delta = event.get("text", "")
                    with self._lock:
                        self._text += delta
                        text_so_far = self._text.strip()
                    if self.on_delta:
                        _safe_call(self.on_delta, delta, text_so_far)
                elif kind == "final":
                    self._on_final(event)
                    return
                elif kind == "error":
                    self._fail(event.get("code"), event.get("message", ""))
                    return
            if not self._done.is_set():
                self._fail(None, "the server closed the connection without a final text")
        except Exception as e:
            if not self._done.is_set():
                self._fail(None, f"connection lost: {e or type(e).__name__}")

    def _on_final(self, event):
        self._final_at = time.time()
        with self._lock:
            self._text = event.get("text", self._text)
            text = self._text.strip()
        self._result = {'text': text, 'model': self.model, 'stats': event.get("stats") or {}}
        self._stopping.set()
        self._done.set()
        if self.on_final:
            _safe_call(self.on_final, self._result['stats'].get("stop_reason"))

    def _fail(self, code, message):
        with self._lock:
            if self._done.is_set():
                return
            prefix = f"otis-speech-server error {code}" if code else "otis-speech-server live session failed"
            error = RuntimeError(f"{prefix}: {message}")
            error.code = code
            error.partial_text = self._text.strip()
            self._error = error
            self._stopping.set()
            self._done.set()
        if self.debug:
            print(f"\nLive transcription failed: {error}")
        if self.on_error and not self._closed_locally:
            _safe_call(self.on_error, error)


def _to_pcm16(samples):
    return (np.clip(samples, -1.0, 1.0) * 32767).astype("<i2").tobytes()


def _safe_call(callback, *args):
    # A failing app callback must not kill the receiver thread and lose the session.
    try:
        callback(*args)
    except Exception:
        traceback.print_exc()
