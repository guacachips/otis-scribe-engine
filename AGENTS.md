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
3. Update README.md if user-facing change

## Releasing a New Version

When user asks to create a new release:

1. **Update version** in `setup.py`:
   - Patch (0.2.0 → 0.2.1): Bug fixes, chores
   - Minor (0.2.0 → 0.3.0): New features
   - Major (0.x.x → 1.0.0): Breaking changes (wait until truly stable)

2. **Commit version bump**:
   ```bash
   git add setup.py
   git commit -m "Bumped to VX.Y.Z"
   git push
   ```

3. **Create and push tag**:
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

**Commit message convention (for actual code changes):**
- `fix:` - Bug fixes
- `feat:` - New features
- `chore:` - Maintenance/cleanup (removing files, dependencies)
- `docs:` - Documentation changes
- No prefix - Version bumps ("Bumped to VX.Y.Z"), initial commits, major releases

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
