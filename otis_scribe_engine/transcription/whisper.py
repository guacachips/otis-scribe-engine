import torch
import time
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from .base import Transcriber
from ..config.model_paths import MODEL_PATHS

@dataclass
class TranscriptionConfig:
    """Configuration for transcription processing"""
    model_id: str = "openai/whisper-tiny"
    device: str = "auto"
    torch_dtype: Optional[torch.dtype] = None
    low_cpu_mem_usage: bool = True
    use_safetensors: bool = True
    force_local: bool = True

class WhisperTranscriber(Transcriber):
    """Local Whisper-based transcription."""

    def __init__(self, model_id="openai/whisper-tiny", device="auto", debug=False):
        """Initialize Whisper transcriber.

        Args:
            model_id: Whisper model identifier (e.g., "openai/whisper-tiny")
            device: Device to use ("auto", "cpu", "cuda", "mps")
            debug: Enable debug mode (detailed metrics)
        """
        self.debug = debug
        self.config = TranscriptionConfig(model_id=model_id, device=device)

        if device == "auto":
            if torch.backends.mps.is_available():
                self.config.device = "mps"
                self.config.torch_dtype = torch.float16
            elif torch.cuda.is_available():
                self.config.device = "cuda"
                self.config.torch_dtype = torch.float16
            else:
                self.config.device = "cpu"
                self.config.torch_dtype = torch.float32
        else:
            self.config.device = device
            if device in ("cuda", "mps"):
                self.config.torch_dtype = torch.float16
            else:
                self.config.torch_dtype = torch.float32

        self.pipe = self._create_pipeline()

    def _create_pipeline(self):
        """Create the Whisper pipeline with configured model"""
        if self.debug:
            print(f"Using device: {self.config.device}")

        local_model_path = None
        if self.config.force_local:
            local_model_path = MODEL_PATHS.get_whisper_model_path(self.config.model_id)
            if local_model_path and MODEL_PATHS.model_exists(local_model_path):
                if self.debug:
                    print(f"Using local model: {local_model_path}")
                model_source = str(local_model_path)
            else:
                if self.debug:
                    print(f"Warning: Local model not found at {local_model_path}")
                    print(f"Falling back to online model: {self.config.model_id}")
                model_source = self.config.model_id
        else:
            model_source = self.config.model_id

        load_kwargs = {
            "torch_dtype": self.config.torch_dtype,
            "low_cpu_mem_usage": self.config.low_cpu_mem_usage,
            "use_safetensors": self.config.use_safetensors
        }

        if local_model_path and MODEL_PATHS.model_exists(local_model_path):
            load_kwargs["local_files_only"] = True

        model = AutoModelForSpeechSeq2Seq.from_pretrained(
            model_source,
            **load_kwargs
        )
        model.to(self.config.device)

        processor = AutoProcessor.from_pretrained(
            model_source,
            local_files_only=local_model_path and MODEL_PATHS.model_exists(local_model_path)
        )

        pipe = pipeline(
            "automatic-speech-recognition",
            model=model,
            tokenizer=processor.tokenizer,
            feature_extractor=processor.feature_extractor,
            torch_dtype=self.config.torch_dtype,
            device=self.config.device,
        )
        return pipe

    def transcribe(self, audio_file_path):
        """Transcribe audio using local Whisper model.

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

        result = self.pipe(str(audio_file_path))
        transcription_time = time.time() - start_time

        return {
            'text': result["text"].strip(),
            'transcription_time': transcription_time,
            'model': self.config.model_id
        }
