from pathlib import Path
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import numpy as np
from typing import Optional, Tuple, Union
import tempfile
import time
from .devices import AudioDeviceManager
from .vad import VoiceActivityDetector, VADConfig

class DeadInputError(RuntimeError):
    """The input device delivered only digital silence (all-zero samples)"""

    def __init__(self, device_name: str):
        super().__init__(f"No signal from input device '{device_name}' (all samples are zero)")
        self.device_name = device_name


class AudioRecorder:
    """Handles audio recording with voice activity detection"""

    DEAD_INPUT_SECONDS = 1.0

    def __init__(self,
                 output_dir: Optional[Path] = None,
                 device_id: Union[int, str, None] = None,
                 vad_config: Optional[VADConfig] = None):
        """
        Initialize the recorder

        Args:
            output_dir (Optional[Path]): Directory to save recordings (uses temp dir if None)
            device_id (Union[int, str, None]): Device ID or device name to record from
                (None follows the macOS default input). Resolved at each record() call.
            vad_config (Optional[VADConfig]): Custom VAD configuration
        """
        self.device_pref = device_id
        self.device_id = None
        self.device_info = None
        self.sample_rate = 16000
        self.block_size = 512
        self.buffer = []

        self.vad = VoiceActivityDetector(vad_config)
        self.output_dir = output_dir
        if self.output_dir:
            self.output_dir.mkdir(parents=True, exist_ok=True)

        self.recording_data = []
        self.is_recording = False
        self.speech_detected = False
        self.start_time = None
        self.duration = 0
        self._stop_requested = False
        self._frames_seen = 0
        self._signal_seen = False
        self._dead_input = False

    def audio_callback(self, indata: np.ndarray, frames: int,
                      time_info: dict, status: sd.CallbackFlags) -> None:
        if status:
            print(f"Status: {status}")

        self._frames_seen += frames
        if not self._signal_seen and np.any(indata):
            self._signal_seen = True

        self.recording_data.extend(indata[:, 0])
        self.buffer.extend(indata[:, 0])

        if len(self.buffer) >= self.block_size:
            audio_chunk = np.array(self.buffer[:self.block_size])
            frame_duration = self.block_size / self.sample_rate

            state, speech_prob, valid_speech = self.vad.process_audio(audio_chunk, frame_duration)

            if valid_speech:
                self.speech_detected = True

            self._show_feedback(speech_prob, valid_speech)

            if self._stop_requested or (self.speech_detected and self.vad.should_stop_recording()):
                self.is_recording = False
                raise sd.CallbackStop()

            self.buffer = self.buffer[self.block_size:]

    def _show_feedback(self, speech_prob: float, valid_speech: bool) -> None:
        """Display recording feedback with validation status"""
        vad_feedback = self.vad.get_state_feedback(speech_prob)

        if not self.speech_detected and speech_prob > self.vad.config.threshold_speech:
            vad_feedback += " (Validating...)"

        current_chunk = np.array(self.recording_data[-1024:]) if self.recording_data else np.array([])
        if len(current_chunk) > 0:
            level = np.max(np.abs(current_chunk))
            level_bar = '=' * int(level * 50)
            print(f"\r{vad_feedback} |{level_bar:<50}|", end='')
        else:
            print(f"\r{vad_feedback}", end='')

    def _resolve_input_device(self) -> None:
        """Re-read the device list and pick the device to open (no stream may be open)"""
        AudioDeviceManager.refresh()
        self.device_id, self.device_info, source = AudioDeviceManager.resolve_input_device(self.device_pref)

        system_default, system_default_error = AudioDeviceManager.get_system_default_input()
        system_default_text = repr(system_default) if system_default else f"<query failed: {system_default_error}>"
        portaudio_default_id = AudioDeviceManager.get_default_devices()[0]
        portaudio_default = AudioDeviceManager.get_device_info(portaudio_default_id)
        portaudio_default_name = portaudio_default['name'] if portaudio_default else None
        print(f"\nRecording device: '{self.device_info['name']}' [#{self.device_id}] via {source}"
              f" | macOS default: {system_default_text}"
              f" | PortAudio default: {portaudio_default_name!r} [#{portaudio_default_id}]")

    def record(self) -> Tuple[Path, float]:
        """
        Start recording with voice activity detection

        Returns:
            Tuple[Path, float]: Audio file path and duration in seconds

        Raises:
            DeadInputError: If the device delivers only zeros, even after one retry
        """
        self.is_recording = True
        self._stop_requested = False
        try:
            self._resolve_input_device()
            self._capture()
            # The retry re-initializes PortAudio: it picks up a default-device change and re-opens the device.
            if self._dead_input and not self._stop_requested:
                print(f"\n\nNo signal from '{self.device_info['name']}', retrying once...")
                self._resolve_input_device()
                self._capture()
                if self._dead_input and not self._stop_requested:
                    raise DeadInputError(self.device_info['name'])
            return self._save_recording()
        finally:
            self.is_recording = False

    def _capture(self) -> None:
        """Record one stream until VAD stop, manual stop, or dead input is detected"""
        print(f"Using sample rate: {self.sample_rate}")
        print("\n🎤 Ready to record. Start speaking...")
        self.recording_data = []
        self.buffer = []
        self.is_recording = True
        self.speech_detected = False
        self._frames_seen = 0
        self._signal_seen = False
        self._dead_input = False
        self.start_time = time.time()
        self.vad.reset()

        dead_input_frames = self.DEAD_INPUT_SECONDS * self.sample_rate
        try:
            with AudioDeviceManager.stream_open(), sd.InputStream(
                device=self.device_id,
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=self.block_size,
                dtype=np.float32
            ):
                while self.is_recording:
                    sd.sleep(100)
                    if not self._signal_seen and self._frames_seen >= dead_input_frames:
                        self._dead_input = True
                        break
                    # A device whose IO proc never fires would otherwise hang this loop forever.
                    if self._frames_seen == 0 and time.time() - self.start_time > 3 * self.DEAD_INPUT_SECONDS:
                        self._dead_input = True
                        break
        except sd.CallbackStop:
            print("\n\nRecording stopped (voice activity ended)")
        except KeyboardInterrupt:
            print("\n\nRecording stopped by user")
        except Exception as e:
            print(f"\n\nError during recording: {e}")
            raise

    def stop_recording(self) -> None:
        """Manually stop recording (override VAD); record() saves and returns the file"""
        if self.is_recording:
            self._stop_requested = True
            while self.is_recording:
                time.sleep(0.1)

    def _save_recording(self) -> Tuple[Path, float]:
        """
        Save the recording to file

        Returns:
            Tuple[Path, float]: Audio file path and duration in seconds

        Raises:
            DeadInputError: If every sample is zero (transcribers hallucinate text on such files)
        """
        if not self.recording_data:
            raise ValueError("No audio data to save")

        audio_data = np.array(self.recording_data)
        peak = np.max(np.abs(audio_data))
        if peak == 0:
            raise DeadInputError(self.device_info['name'])
        audio_data = audio_data / peak

        self.duration = time.time() - self.start_time if self.start_time else 0

        if self.output_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            file_path = self.output_dir / filename
        else:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            file_path = Path(temp_file.name)

        sf.write(str(file_path), audio_data, self.sample_rate)
        print(f"\nRecording saved: {file_path}")

        return file_path, self.duration
