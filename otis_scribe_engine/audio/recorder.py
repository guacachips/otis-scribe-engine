from pathlib import Path
from datetime import datetime
import sounddevice as sd
import soundfile as sf
import numpy as np
from typing import Optional, Tuple
import tempfile
import time
from .devices import AudioDeviceManager
from .vad import VoiceActivityDetector, VADConfig

class AudioRecorder:
    """Handles audio recording with voice activity detection"""

    def __init__(self,
                 output_dir: Optional[Path] = None,
                 device_id: Optional[int] = None,
                 vad_config: Optional[VADConfig] = None):
        """
        Initialize the recorder

        Args:
            output_dir (Optional[Path]): Directory to save recordings (uses temp dir if None)
            device_id (Optional[int]): Specific device ID to use
            vad_config (Optional[VADConfig]): Custom VAD configuration
        """
        self.device_id = device_id or AudioDeviceManager.get_default_devices()[0]
        valid, message, device_info = AudioDeviceManager.validate_device(self.device_id)
        if not valid:
            raise ValueError(f"Invalid audio device: {message}")
        self.device_info = device_info
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

    def audio_callback(self, indata: np.ndarray, frames: int,
                      time_info: dict, status: sd.CallbackFlags) -> None:
        if status:
            print(f"Status: {status}")

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

    def record(self) -> Tuple[Path, float]:
        """
        Start recording with voice activity detection

        Returns:
            Tuple[Path, Path]: Paths to the timestamped and latest recordings
        """
        print(f"\nInitializing recording device: {self.device_info['name']}")
        print(f"Using sample rate: {self.sample_rate}")
        print("\n🎤 Ready to record. Start speaking...")
        self.recording_data = []
        self.buffer = []
        self.is_recording = True
        self.speech_detected = False
        self._stop_requested = False
        self.start_time = time.time()
        self.vad.reset()

        try:
            with sd.InputStream(
                device=self.device_id,
                channels=1,
                samplerate=self.sample_rate,
                callback=self.audio_callback,
                blocksize=self.block_size,
                dtype=np.float32
            ):
                while self.is_recording:
                    sd.sleep(100)
        except sd.CallbackStop:
            print("\n\nRecording stopped (voice activity ended)")
        except KeyboardInterrupt:
            print("\n\nRecording stopped by user")
        except Exception as e:
            print(f"\n\nError during recording: {e}")
            raise
        finally:
            self.is_recording = False

        return self._save_recording()

    def stop_recording(self) -> Tuple[Path, float]:
        """
        Manually stop recording (override VAD)

        Returns:
            Tuple[Path, float]: Audio file path and duration
        """
        if self.is_recording:
            self._stop_requested = True
            while self.is_recording:
                time.sleep(0.1)

        return self._save_recording() if self.recording_data else (None, 0)

    def _save_recording(self) -> Tuple[Path, float]:
        """
        Save the recording to file

        Returns:
            Tuple[Path, float]: Audio file path and duration in seconds
        """
        if not self.recording_data:
            raise ValueError("No audio data to save")

        audio_data = np.array(self.recording_data)
        if np.max(np.abs(audio_data)) > 0:
            audio_data = audio_data / np.max(np.abs(audio_data))

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
