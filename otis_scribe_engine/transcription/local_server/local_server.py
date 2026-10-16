import json
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from ..base import Transcriber

DEFAULT_BASE_URL = "http://127.0.0.1:6847"
DEFAULT_MODEL = "voxtral-realtime-4bit"

# A proxy from HTTP_PROXY or the macOS network settings must never relay requests to a local server.
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class LocalServerUnavailableError(ConnectionError):
    """Raised when otis-speech-server cannot be reached."""

    def __init__(self, base_url):
        self.base_url = base_url
        super().__init__(
            f"otis-speech-server is not running at {base_url}. "
            "Start it with: conda activate otis-speech-server; otis-speech-server"
        )


class LocalServerTranscriber(Transcriber):
    """Transcription through a local otis-speech-server (MLX models on Apple Silicon)."""

    def __init__(self, base_url=DEFAULT_BASE_URL, model=DEFAULT_MODEL, language=None, timeout=600, debug=False):
        """Initialize local server transcriber.

        Args:
            base_url: otis-speech-server address
            model: Server model id (e.g., "voxtral-realtime-4bit", "whisper-large-v3-turbo")
            language: Language code (e.g., "fr") or None for auto-detection (Voxtral ignores it)
            timeout: Seconds to wait for a transcription (the first request also loads the model)
            debug: Enable debug output
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.language = language
        self.timeout = timeout
        self.debug = debug

    def status(self):
        """Return the server's GET /status payload."""
        return self._request("GET", "/status", timeout=5)

    def transcribe(self, audio_file_path):
        """Transcribe audio through otis-speech-server.

        Returns:
            dict: {'text': str, 'transcription_time': float, 'model': str}

        Raises:
            LocalServerUnavailableError: the server is not reachable
            RuntimeError: the server answered with an error (message from the server)
        """
        path = Path(audio_file_path)
        fields = {"model": self.model, "response_format": "json"}
        if self.language:
            fields["language"] = self.language
        body, content_type = _encode_multipart(fields, path.name, path.read_bytes())

        if self.debug:
            print(f"Transcribing with otis-speech-server at {self.base_url}, model: {self.model}")
            print(f"Audio file: {audio_file_path}")

        start_time = time.time()
        response = self._request(
            "POST", "/v1/audio/transcriptions",
            body=body, headers={"Content-Type": content_type}, timeout=self.timeout
        )
        transcription_time = time.time() - start_time

        text = response.get("text") if isinstance(response, dict) else None
        if not isinstance(text, str):
            raise RuntimeError(f"otis-speech-server response has no 'text': {response!r:.200}")

        if self.debug:
            print(f"Transcription completed in {transcription_time:.2f}s")

        return {
            'text': text.strip(),
            'transcription_time': transcription_time,
            'model': self.model
        }

    def _request(self, method, path, body=None, headers=None, timeout=None):
        request = urllib.request.Request(self.base_url + path, data=body, headers=headers or {}, method=method)
        try:
            with _OPENER.open(request, timeout=timeout) as response:
                payload = response.read()
        # HTTPError subclasses URLError: it must be caught first, it means the server is up.
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"otis-speech-server error {e.code}: {_error_message(e)}") from None
        except urllib.error.URLError as e:
            if isinstance(e.reason, TimeoutError):
                raise TimeoutError(f"otis-speech-server at {self.base_url} did not answer within {timeout}s") from None
            raise LocalServerUnavailableError(self.base_url) from e
        except TimeoutError:
            raise TimeoutError(f"otis-speech-server at {self.base_url} did not answer within {timeout}s") from None
        except ConnectionError as e:
            raise LocalServerUnavailableError(self.base_url) from e

        try:
            return json.loads(payload)
        except ValueError:
            raise RuntimeError(f"otis-speech-server returned a non-JSON response: {payload[:200]!r}") from None


def _error_message(http_error):
    body = http_error.read()
    try:
        return json.loads(body)["error"]["message"]
    except (ValueError, KeyError, TypeError):
        return body.decode("utf-8", "replace").strip() or http_error.reason


def _encode_multipart(fields, filename, content):
    boundary = uuid.uuid4().hex
    parts = [
        f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode("utf-8")
        for name, value in fields.items()
    ]
    safe_filename = filename.replace('"', "").replace("\r", "").replace("\n", "")
    parts.append(
        f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{safe_filename}"\r\n'
        f'Content-Type: audio/wav\r\n\r\n'.encode("utf-8")
    )
    parts.append(content)
    parts.append(f"\r\n--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"
