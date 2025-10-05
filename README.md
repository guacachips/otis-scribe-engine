# Otis Scribe Engine

Voice recording with VAD auto-stop + transcription (Whisper/Gemini).

## Development Setup

```bash
pip install -e ".[all]"
```

## Structure

- `audio/` - VAD-based recording (Silero VAD)
- `transcription/` - Whisper (openai-whisper) and Gemini backends
- `config/` - User settings, model paths

## Note

Uses `openai-whisper` (not transformers) for better performance and turbo model support.
