import os
import time
from pathlib import Path
from mistralai import Mistral
from mistralai.models import File
from dotenv import load_dotenv
from ..base import Transcriber

class MistralTranscriber(Transcriber):
    """Mistral API-based transcription using Voxtral models."""

    def __init__(self, model="voxtral-mini-latest", api_key=None, debug=False):
        """Initialize Mistral transcriber.

        Args:
            model: Mistral model identifier (e.g., "voxtral-mini-latest")
            api_key: Mistral API key (if None, loads from environment)
            debug: Enable debug mode (detailed metrics)
        """
        load_dotenv()

        if api_key is None:
            api_key = os.environ.get("MISTRAL_API_KEY")

        if not api_key:
            raise ValueError("MISTRAL_API_KEY not found in environment")

        self.client = Mistral(api_key=api_key)
        self.model = model
        self.debug = debug

    def transcribe(self, audio_file_path):
        """Transcribe audio using Mistral API.

        Args:
            audio_file_path: Path to audio file

        Returns:
            dict: {
                'text': str,
                'transcription_time': float,
                'model': str
            }
        """
        start_time = time.time()

        if self.debug:
            print(f"Transcribing with Mistral model: {self.model}")
            print(f"Audio file: {audio_file_path}")

        with open(audio_file_path, "rb") as audio_file:
            file_obj = File(
                file_name=Path(audio_file_path).name,
                content=audio_file
            )
            response = self.client.audio.transcriptions.complete(
                model=self.model,
                file=file_obj
            )

        transcription_time = time.time() - start_time

        if self.debug:
            print(f"Transcription completed in {transcription_time:.2f}s")
            if hasattr(response, 'language'):
                print(f"Detected language: {response.language}")

        return {
            'text': response.text.strip(),
            'transcription_time': transcription_time,
            'model': self.model
        }
