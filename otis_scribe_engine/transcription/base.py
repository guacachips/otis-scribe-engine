from abc import ABC, abstractmethod

class Transcriber(ABC):
    """Abstract base class for transcription engines."""

    @abstractmethod
    def transcribe(self, audio_file_path):
        """Transcribe an audio file to text.

        Args:
            audio_file_path: Path to the audio file

        Returns:
            dict: Transcription result with at minimum:
                {
                    'text': str,
                    'transcription_time': float
                }
        """
        pass
