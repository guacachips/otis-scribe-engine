# Otis Scribe Engine

Voice recording and transcription engine with Voice Activity Detection (VAD) and multiple transcription backends.

## Features

- 🎤 **Automatic recording** with VAD-based silence detection
- 🤖 **Multiple transcription backends**:
  - Local Whisper (offline, private, free)
  - Google Gemini API (fast, cloud-based)
- 🔧 **Extensible architecture** for adding new backends
- 📦 **Optional dependencies** - install only what you need
- ⚙️ **Configurable** - VAD thresholds, model selection, user preferences

## Installation

### Minimal (Gemini only)
```bash
pip install git+https://github.com/guacachips/otis-scribe-engine.git#egg=otis-scribe-engine[gemini]
```

### With Whisper support
```bash
pip install git+https://github.com/guacachips/otis-scribe-engine.git#egg=otis-scribe-engine[whisper]
```

### Everything
```bash
pip install git+https://github.com/guacachips/otis-scribe-engine.git#egg=otis-scribe-engine[all]
```

### Local development
```bash
git clone https://github.com/guacachips/otis-scribe-engine.git
cd otis-scribe-engine
pip install -e ".[all]"
```

## Quick Start

### Recording with VAD

```python
from otis_scribe_engine import AudioRecorder, VADConfig

vad_config = VADConfig(
    threshold_speech=0.5,
    silence_duration_max=2.5,
    min_speech_duration=0.5
)

recorder = AudioRecorder(vad_config=vad_config)
audio_file, duration = recorder.record()
print(f"Recorded {duration:.2f}s of audio to {audio_file}")
```

### Transcription with Whisper

```python
from otis_scribe_engine import get_transcriber

transcriber = get_transcriber("whisper", model_id="openai/whisper-tiny")
result = transcriber.transcribe(audio_file)
print(f"Transcription: {result['text']}")
print(f"Time: {result['transcription_time']:.2f}s")
```

### Transcription with Gemini

```python
from otis_scribe_engine import get_transcriber

transcriber = get_transcriber("gemini", api_key="your-api-key", debug=True)
result = transcriber.transcribe(audio_file)
print(f"Transcription: {result['text']}")

if 'tokens' in result:
    print(f"Tokens: {result['tokens']['total_tokens']}")
    print(f"Cost: ${result['tokens']['total_cost']:.6f}")
```

### User Settings

```python
from otis_scribe_engine import UserSettings

settings = UserSettings.load()
settings.transcription_engine = "whisper"
settings.whisper_model = "base"
settings.save()
```

## Downloading Models

For offline Whisper usage, download models first:

```python
from otis_scribe_engine.scripts.download_models import ModelDownloader

downloader = ModelDownloader()
downloader.download_whisper_models()
```

Or from command line:
```bash
python -m otis_scribe_engine.scripts.download_models
```

## Configuration

### VAD Configuration

```python
from otis_scribe_engine import VADConfig

config = VADConfig(
    threshold_speech=0.5,           # Speech detection sensitivity (0-1)
    silence_duration_short=0.8,     # Brief pauses (seconds)
    silence_duration_long=1.5,      # Sentence pauses (seconds)
    silence_duration_max=2.5,       # Auto-stop threshold (seconds)
    min_speech_duration=0.5         # Minimum valid speech (seconds)
)
```

### User Preferences

Settings are persisted to `~/.otis-scribe-engine/config.json`:

```json
{
  "transcription_engine": "gemini",
  "whisper_model": "tiny"
}
```

### Model Storage

Whisper models are stored in `~/.otis-scribe-engine/models/whisper/`

## API Reference

### AudioRecorder

```python
class AudioRecorder:
    def __init__(self, vad_config: Optional[VADConfig] = None)
    def record(self) -> Tuple[Path, float]
    def stop_recording(self) -> Tuple[Path, float]
    @property
    def is_recording(self) -> bool
```

### Transcriber

```python
class Transcriber(ABC):
    @abstractmethod
    def transcribe(self, audio_file_path) -> dict
```

Both `GeminiTranscriber` and `WhisperTranscriber` return:
```python
{
    'text': str,                    # Transcribed text
    'transcription_time': float,    # Processing time in seconds
    'tokens': dict,                 # (Gemini only, if debug=True)
    'model': str                    # (Whisper only)
}
```

### get_transcriber()

```python
def get_transcriber(engine: str, **kwargs) -> Transcriber:
    """
    engine: "gemini" or "whisper"

    Gemini kwargs:
        api_key: str (optional, reads from GOOGLE_API_KEY env var)
        debug: bool (default False, enables token counting)

    Whisper kwargs:
        model_id: str (default "openai/whisper-tiny")
        device: str (default "auto", options: "cpu", "cuda", "mps")
        debug: bool (default False)
    """
```

## Used By

- [otis-dictation-macos-app](https://github.com/guacachips/otis-dictation-macos-app) - macOS menu bar dictation tool
- [Agent Vero](https://github.com/guacachips/agent-vero) - Full voice assistant

## Development

```bash
git clone https://github.com/guacachips/otis-scribe-engine.git
cd otis-scribe-engine
pip install -e ".[all]"
pytest tests/
```

## License

MIT License - see LICENSE file for details

## Credits

- Silero VAD: https://github.com/snakers4/silero-vad (MIT License)
- Whisper: https://github.com/openai/whisper
- Gemini API: https://ai.google.dev/
