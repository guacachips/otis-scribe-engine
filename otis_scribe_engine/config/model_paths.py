from pathlib import Path
from dataclasses import dataclass
from typing import Optional

@dataclass
class ModelPaths:
    """Centralized configuration for local model paths"""

    models_root: Path = Path.home() / ".otis-scribe-engine" / "models"

    whisper_tiny: Path = models_root / "whisper" / "whisper-tiny"
    whisper_base: Path = models_root / "whisper" / "whisper-base"
    whisper_large_turbo: Path = models_root / "whisper" / "whisper-large-v3-turbo"

    def __post_init__(self):
        """Ensure all paths are absolute"""
        for field_name in self.__dataclass_fields__:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Path):
                setattr(self, field_name, field_value.resolve())

    def create_directories(self):
        """Create all model directories if they don't exist"""
        for field_name in self.__dataclass_fields__:
            field_value = getattr(self, field_name)
            if isinstance(field_value, Path) and field_name != "models_root":
                field_value.mkdir(parents=True, exist_ok=True)

    def get_whisper_model_path(self, model_name: str) -> Optional[Path]:
        """Get the local path for a Whisper model"""
        model_mapping = {
            "openai/whisper-tiny": self.whisper_tiny,
            "openai/whisper-base": self.whisper_base,
            "openai/whisper-large-v3-turbo": self.whisper_large_turbo,
        }
        return model_mapping.get(model_name)

    def model_exists(self, model_path: Path) -> bool:
        """Check if a model exists locally"""
        return model_path.exists() and any(model_path.iterdir())

MODEL_PATHS = ModelPaths()
