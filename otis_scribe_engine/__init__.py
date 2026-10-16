from pathlib import Path

__version__ = "0.4.0"
PACKAGE_ROOT = Path(__file__).parent

from .audio import AudioRecorder, DeadInputError, VADConfig, AudioDeviceManager
from .transcription import get_transcriber, Transcriber, LocalServerTranscriber, LocalServerUnavailableError
from .config import MODEL_PATHS

__all__ = [
    'AudioRecorder',
    'DeadInputError',
    'VADConfig',
    'AudioDeviceManager',
    'get_transcriber',
    'Transcriber',
    'LocalServerTranscriber',
    'LocalServerUnavailableError',
    'MODEL_PATHS',
    '__version__',
]
