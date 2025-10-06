from dataclasses import dataclass

@dataclass
class TranscriptionConfig:
    """Transcription configuration (pure data, no persistence)"""
    transcription_engine: str = "gemini"
    whisper_model: str = "tiny"
    language: str = "fr"
