from .base import Transcriber
from .gemini import GeminiTranscriber
from .whisper import WhisperTranscriber
from .mistral_api import MistralTranscriber

def get_transcriber(engine: str, **kwargs) -> Transcriber:
    if engine == "gemini":
        return GeminiTranscriber(**kwargs)
    elif engine == "whisper":
        return WhisperTranscriber(**kwargs)
    elif engine == "mistral":
        return MistralTranscriber(**kwargs)
    else:
        raise ValueError(f"Unknown transcription engine: {engine}")

__all__ = ['Transcriber', 'GeminiTranscriber', 'WhisperTranscriber', 'MistralTranscriber', 'get_transcriber']
