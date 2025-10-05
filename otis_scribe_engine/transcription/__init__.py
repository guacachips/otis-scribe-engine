from .base import Transcriber
from .gemini import GeminiTranscriber
from .whisper import WhisperTranscriber

def get_transcriber(engine: str, **kwargs) -> Transcriber:
    if engine == "gemini":
        return GeminiTranscriber(**kwargs)
    elif engine == "whisper":
        return WhisperTranscriber(**kwargs)
    else:
        raise ValueError(f"Unknown transcription engine: {engine}")

__all__ = ['Transcriber', 'GeminiTranscriber', 'WhisperTranscriber', 'get_transcriber']
