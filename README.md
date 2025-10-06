# Otis Scribe Engine

Voice recording with VAD auto-stop + transcription (Whisper/Gemini/Mistral).

## Installation

```bash
pip install -e ".[all]"          # All backends
pip install -e ".[whisper]"      # Local Whisper only
pip install -e ".[gemini]"       # Gemini API only
pip install -e ".[mistral]"      # Mistral API only
```

## Usage

```python
from otis_scribe_engine import AudioRecorder, get_transcriber

# Record audio
recorder = AudioRecorder()
audio_path, duration = recorder.record()

# Transcribe with Whisper (local, no API key)
transcriber = get_transcriber("whisper", model_id="tiny")
result = transcriber.transcribe(audio_path)

# Transcribe with Gemini (requires GOOGLE_API_KEY env var)
transcriber = get_transcriber("gemini")
result = transcriber.transcribe(audio_path)

# Transcribe with Mistral (requires MISTRAL_API_KEY env var)
transcriber = get_transcriber("mistral")
result = transcriber.transcribe(audio_path)
```

## Structure

- `audio/` - VAD-based recording (Silero VAD)
- `transcription/` - Whisper (openai-whisper), Gemini, and Mistral backends
- `config/` - User settings, model paths

## Note

Uses `openai-whisper` (not transformers) for better performance and turbo model support.

## Contributing

**Development Setup:**
```bash
# 1. Install dependencies
pip install -e ".[all,dev]"  # Install all backends + dev tools (pytest)

# 2. Configure API keys
cp .env.example .env
# Edit .env and add your API keys
```

**Running Tests:**
```bash
make test  # Run integration tests

# Or manually:
python -m pytest otis_scribe_engine/transcription/ -v
```

**Note:** Integration tests require API keys in `.env` file (`MISTRAL_API_KEY`, `GOOGLE_API_KEY`). Tests will skip if keys are not set.
