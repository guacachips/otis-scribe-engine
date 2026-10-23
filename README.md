# Otis Scribe Engine

Voice recording with VAD auto-stop + transcription (Whisper/Gemini/Mistral/local otis-speech-server).

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

# Record audio (device_id: None follows the macOS default, or pass a device name/ID;
# record() raises DeadInputError if the device delivers only silence)
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

# Transcribe with a running otis-speech-server (local MLX models, no API key;
# raises LocalServerUnavailableError if the server is not running)
transcriber = get_transcriber("local-server", model="voxtral-realtime-4bit")  # or "whisper-large-v3-turbo", language="fr"
result = transcriber.transcribe(audio_path)
```

### Live transcription (otis-speech-server ≥ 0.2.0, Voxtral only)

Text arrives while you talk. Callbacks run on a background thread.

```python
from otis_scribe_engine import AudioRecorder, LocalServerLiveTranscriber, VADConfig

live = LocalServerLiveTranscriber(on_delta=lambda delta, text_so_far: print(text_so_far))
live.start()  # raises LocalServerUnavailableError if the server is not running
recorder = AudioRecorder(vad_config=VADConfig(silence_duration_max=10.0), on_audio=live.feed)
recorder.record()
result = live.finish()  # {'text', 'transcription_time', 'model', 'stats'}; RuntimeError (.code, .partial_text) on failure
```

## Structure

- `audio/` - VAD-based recording (Silero VAD)
- `transcription/` - Whisper (openai-whisper), Gemini, Mistral, and local server (`otis-speech-server` over HTTP, live over WebSocket) backends
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

**Note:** Integration tests require API keys in `.env` file (`MISTRAL_API_KEY`, `GOOGLE_API_KEY`). Tests will skip if keys are not set. The local server test skips unless `otis-speech-server` is running (`OTIS_SPEECH_SERVER_URL` / `OTIS_SPEECH_SERVER_MODEL` override address and model).
