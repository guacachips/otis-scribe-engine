from pathlib import Path

__version__ = "0.1.0"
PACKAGE_ROOT = Path(__file__).parent

from .audio import AudioRecorder, VADConfig, AudioDeviceManager
from .transcription import get_transcriber, Transcriber
from .config import MODEL_PATHS

__all__ = [
    'AudioRecorder',
    'VADConfig',
    'AudioDeviceManager',
    'get_transcriber',
    'Transcriber',
    'MODEL_PATHS',
    '__version__',
]
