from pathlib import Path

__version__ = "0.3.2"
PACKAGE_ROOT = Path(__file__).parent

from .audio import AudioRecorder, DeadInputError, VADConfig, AudioDeviceManager
from .transcription import get_transcriber, Transcriber
from .config import MODEL_PATHS

__all__ = [
    'AudioRecorder',
    'DeadInputError',
    'VADConfig',
    'AudioDeviceManager',
    'get_transcriber',
    'Transcriber',
    'MODEL_PATHS',
    '__version__',
]
