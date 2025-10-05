"""
Whisper-based transcription module using official openai-whisper package.

This module was migrated from transformers to openai-whisper to avoid breaking changes
in transformers 4.50+ that caused incomplete transcriptions.

Note: openai-whisper does not support MPS (Apple Metal) due to sparse tensor limitations.
However, CPU performance is excellent - typically 7-10x faster than the previous
transformers-based implementation even with MPS acceleration.

See PERFORMANCE_COMPARISON.md for benchmarks.
"""

import whisper
import time
import torch
from typing import Optional
from .base import Transcriber


class WhisperTranscriber(Transcriber):
    """Local Whisper-based transcription using openai-whisper."""

    # Model name mapping: HuggingFace names -> openai-whisper names
    MODEL_NAME_MAP = {
        "openai/whisper-tiny": "tiny",
        "openai/whisper-base": "base",
        "openai/whisper-small": "small",
        "openai/whisper-medium": "medium",
        "openai/whisper-large": "large",
        "openai/whisper-large-v2": "large-v2",
        "openai/whisper-large-v3": "large-v3",
        "openai/whisper-large-v3-turbo": "turbo",
        # Also support direct names
        "tiny": "tiny",
        "base": "base",
        "small": "small",
        "medium": "medium",
        "large": "large",
        "turbo": "turbo",
    }

    def __init__(self, model_id="openai/whisper-tiny", device="auto", debug=False, language=None):
        """Initialize Whisper transcriber.

        Args:
            model_id: Whisper model identifier (e.g., "openai/whisper-tiny" or "tiny")
            device: Device to use ("auto", "cpu", "cuda") - Note: MPS not supported
            debug: Enable debug mode (detailed metrics)
            language: Language code (e.g., "fr", "en") or None for auto-detection
        """
        self.debug = debug
        self.language = language
        self.model_id_original = model_id

        # Convert model name if needed
        self.model_name = self.MODEL_NAME_MAP.get(model_id, model_id)

        # Determine device (Note: openai-whisper doesn't support MPS)
        if device == "auto":
            if torch.cuda.is_available():
                self.device = "cuda"
            else:
                self.device = "cpu"
                if torch.backends.mps.is_available() and self.debug:
                    print("⚠️  MPS available but not supported by openai-whisper - using CPU")
        else:
            if device == "mps":
                print("⚠️  MPS not supported by openai-whisper - falling back to CPU")
                self.device = "cpu"
            else:
                self.device = device

        if self.debug:
            print(f"Loading Whisper model: {self.model_name}")
            print(f"Device: {self.device}")

        # Load model
        start_time = time.time()
        self.model = whisper.load_model(self.model_name, device=self.device)
        load_time = time.time() - start_time

        if self.debug:
            print(f"Model loaded in {load_time:.2f}s")

    def transcribe(self, audio_file_path):
        """Transcribe audio using openai-whisper.

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
            print(f"Transcribing audio file: {audio_file_path}")

        # Transcribe with language parameter if specified
        transcribe_kwargs = {}
        if self.language:
            transcribe_kwargs['language'] = self.language
            if self.debug:
                print(f"Using language: {self.language}")

        result = self.model.transcribe(str(audio_file_path), **transcribe_kwargs)
        transcription_time = time.time() - start_time

        if self.debug:
            print(f"Transcription completed in {transcription_time:.2f}s")
            print(f"Detected language: {result.get('language', 'N/A')}")
            print(f"Segments: {len(result.get('segments', []))}")

        return {
            'text': result['text'].strip(),
            'transcription_time': transcription_time,
            'model': self.model_id_original
        }
