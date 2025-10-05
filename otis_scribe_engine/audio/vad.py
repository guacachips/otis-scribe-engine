import torch
from enum import Enum
from typing import Optional
import numpy as np
from dataclasses import dataclass

class VoiceState(Enum):
    """Enum for different voice activity states"""
    SPEECH = "SPEECH"
    SHORT_PAUSE = "SHORT_PAUSE"
    LONG_PAUSE = "LONG_PAUSE"
    SILENCE = "SILENCE"

@dataclass
class VADConfig:
    """Configuration for Voice Activity Detection"""
    sample_rate: int = 16000
    threshold_speech: float = 0.5
    silence_duration_short: float = 0.8
    silence_duration_long: float = 1.5
    silence_duration_max: float = 2.5
    min_speech_duration: float = 0.5

class VoiceActivityDetector:
    """Handles voice activity detection using Silero VAD"""

    def __init__(self, config: Optional[VADConfig] = None):
        """
        Initialize VAD with optional custom configuration

        Args:
            config (Optional[VADConfig]): Custom configuration for VAD
        """
        self.config = config or VADConfig()

        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False
        )
        self.model = model
        self.model.eval()

        self.silence_duration = 0.0
        self.speech_duration = 0.0
        self.current_state = VoiceState.SILENCE
        self.valid_speech_detected = False

    def process_audio(self, audio_chunk: np.ndarray,
                     frame_duration: float) -> tuple[VoiceState, float]:
        """
        Process an audio chunk and determine voice activity

        Args:
            audio_chunk (np.ndarray): Audio data chunk
            frame_duration (float): Duration of the audio chunk in seconds

        Returns:
            tuple[VoiceState, float]: Current voice state and speech probability
        """
        required_samples = 512
        if len(audio_chunk) != required_samples:
            if len(audio_chunk) < required_samples:
                audio_chunk = np.pad(audio_chunk, (0, required_samples - len(audio_chunk)))
            else:
                audio_chunk = audio_chunk[:required_samples]

        audio_tensor = torch.from_numpy(audio_chunk).float()
        if torch.max(torch.abs(audio_tensor)) > 0:
            audio_tensor = audio_tensor / torch.max(torch.abs(audio_tensor))

        with torch.no_grad():
            speech_prob = self.model(audio_tensor, self.config.sample_rate).item()

        if speech_prob > self.config.threshold_speech:
            self.silence_duration = 0.0
            self.speech_duration += frame_duration
            self.current_state = VoiceState.SPEECH

            if self.speech_duration >= self.config.min_speech_duration:
                self.valid_speech_detected = True
        else:
            self.silence_duration += frame_duration
            self.speech_duration = 0.0
            self._update_state_based_on_silence()

        return self.current_state, speech_prob, self.valid_speech_detected

    def _update_state_based_on_silence(self):
        """Update the voice state based on silence duration"""
        if self.silence_duration >= self.config.silence_duration_max:
            if self.current_state != VoiceState.SILENCE:
                print(f"\nSilence threshold reached ({self.silence_duration:.2f}s)")
                self.current_state = VoiceState.SILENCE
        elif self.silence_duration >= self.config.silence_duration_long:
            self.current_state = VoiceState.LONG_PAUSE
        elif self.silence_duration >= self.config.silence_duration_short:
            self.current_state = VoiceState.SHORT_PAUSE

    def should_stop_recording(self) -> bool:
        """
        Determine if recording should stop based on current state

        Returns:
            bool: True if recording should stop
        """
        return self.current_state == VoiceState.SILENCE

    def get_state_feedback(self, speech_prob: float) -> str:
        """
        Get human-readable feedback about current state

        Args:
            speech_prob (float): Current speech probability

        Returns:
            str: Formatted feedback string
        """
        state_indicators = {
            VoiceState.SPEECH: "🎤 Speaking",
            VoiceState.SHORT_PAUSE: "⏸️ Brief pause",
            VoiceState.LONG_PAUSE: "⏸️ Long pause",
            VoiceState.SILENCE: "⏹️ Silence detected"
        }

        return f"{state_indicators[self.current_state]} (Speech prob: {speech_prob:.2f})"

    def reset(self):
        """Reset the VAD state"""
        self.silence_duration = 0.0
        self.speech_duration = 0.0
        self.current_state = VoiceState.SILENCE
        self.valid_speech_detected = False
