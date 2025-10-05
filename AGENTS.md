# AGENTS.md - Instructions for AI Coding Agents

## Testing Philosophy

**No unit tests** - The codebase is small enough (~1000 lines) that unit tests provide no value.

**Testing approach:**
- Manual testing via the macOS app (otis-dictation-macos-app)
- Quick smoke tests by importing and creating objects in Python REPL
- Integration tests only when adding complex features

**Do NOT:**
- Add pytest tests for basic imports/object creation
- Test things that would obviously crash if broken
- Write tests that don't test actual functionality

## Development Setup

```bash
pip install -e ".[all]"
```

## Code Principles

1. **Small codebase** (~1000 lines) - Don't add unnecessary complexity
2. **No verbose docs** - Code should be self-explanatory
3. **Test after refactoring** - See "Critical Rule" above
4. **Minimal dependencies** - Only add if truly needed

## Architecture

- `audio/` - VAD recording (don't touch unless audio issues)
- `transcription/whisper.py` - Uses openai-whisper (not transformers!)
- `transcription/gemini.py` - Gemini API wrapper
- `config/` - Settings, model paths

## Key Decisions

- **openai-whisper over transformers**: transformers 4.50+ broke Whisper. Don't add transformers back.
- **No MPS support**: openai-whisper limitation, but CPU is faster anyway.
- **Auto model download**: Models download on first use to ~/.cache/whisper/

## When Changing Dependencies

1. Update `setup.py`
2. Test with `pip install -e ".[all]"` in fresh env
3. Run full test suite
4. Update README.md if user-facing change

## How to Verify Changes

1. **Import test** - Does it import without crashing?
   ```bash
   python -c "from otis_scribe_engine import get_transcriber, AudioRecorder"
   ```

2. **App test** - Does the macOS app still work?
   ```bash
   cd ../otis-dictation-macos-app
   python app.py
   # Record something and verify transcription works
   ```

## What NOT to Do

- ❌ Add transformers dependency back
- ❌ Write verbose documentation
- ❌ Add useless unit tests
- ❌ Make README longer than code
- ❌ Add complexity without reason
