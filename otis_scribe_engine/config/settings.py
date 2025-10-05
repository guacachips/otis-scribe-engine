import json
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class UserSettings:
    """User preferences for transcription"""
    transcription_engine: str = "gemini"
    whisper_model: str = "tiny"
    language: str = "fr"  # Default to French, change to "en" for English or None for auto-detect

    @classmethod
    def get_config_path(cls) -> Path:
        """Get the configuration file path"""
        return Path.home() / ".otis-scribe-engine" / "config.json"

    @classmethod
    def load(cls) -> 'UserSettings':
        """Load settings from config file or return defaults"""
        config_file = cls.get_config_path()
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    data = json.load(f)
                return cls(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"Warning: Failed to load settings from {config_file}: {e}")
                print("Using default settings")
        return cls()

    def save(self):
        """Save settings to config file"""
        config_dir = self.get_config_path().parent
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = self.get_config_path()

        with open(config_file, 'w') as f:
            json.dump(asdict(self), f, indent=2)
