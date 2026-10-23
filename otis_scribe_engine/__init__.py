from pathlib import Path

__version__ = "0.5.0"
PACKAGE_ROOT = Path(__file__).parent

from .audio import AudioRecorder, DeadInputError, VADConfig, AudioDeviceManager
from .transcription import (get_transcriber, Transcriber, LocalServerTranscriber, LocalServerLiveTranscriber,
                            LocalServerUnavailableError)
from .config import MODEL_PATHS

__all__ = [
    'AudioRecorder',
    'DeadInputError',
    'VADConfig',
    'AudioDeviceManager',
    'get_transcriber',
    'Transcriber',
    'LocalServerTranscriber',
    'LocalServerLiveTranscriber',
    'LocalServerUnavailableError',
    'MODEL_PATHS',
    '__version__',
]
