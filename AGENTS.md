# AGENTS.md - Instructions for AI Coding Agents

## Testing Philosophy

**Context:** This library is used by multiple client apps (macOS, iOS, Web API). Our users are app developers who depend on a stable contract.

**Why integration tests only:**
- Mocked tests give false confidence (pass even when real provider APIs break)
- Real breakage happens when: provider SDK updates, API changes, auth methods change
- Library logic is simple (~50 lines per provider) - mocks test nothing useful
- Integration tests catch what actually breaks in production

**Test strategy:**
- Each provider gets ONE integration test in its subfolder (e.g., `mistral_api/test_mistral.py`)
- Test verifies the contract: `{'text': str, 'transcription_time': float, 'model': str}`
- Tests use real API + real audio (`test_fixtures/sample.wav`)
- Skip automatically if API keys not in `.env` (safe for CI/local)

**Pre-release workflow (CRITICAL):**
```bash
# Before tagging any release
make test  # All integration tests must pass

# If any fail: provider API broke, fix before releasing
```

**Adding new providers:**
1. Create `transcription/provider_name/` subfolder
2. Add provider implementation + `test_provider.py` (co-located)
3. One integration test verifying the contract
4. Update `.env.example` with required API key

**Running tests:**
```bash
make test                    # All providers
make test                    # Uses .env for API keys
python -m pytest path/to/test_provider.py -v  # Specific provider
```

**Do NOT:**
- Mock external APIs (defeats the purpose)
- Test imports or trivial code
- Add tests without real value

## Development Setup

```bash
# Install dependencies
pip install -e ".[all,dev]"

# Configure API keys
cp .env.example .env
# Edit .env and add your actual API keys
```

## Code Principles

1. **Correctness and clarity first** - Speed and efficiency are secondary unless specified
2. **No summary comments** - Only write comments to explain "why" for tricky/non-obvious code
3. **Prefer existing files** - Only create new files for new logical components
4. **Small codebase** (~1000 lines) - Don't add unnecessary complexity
5. **Self-explanatory code** - Code should be readable without verbose docs
6. **Minimal dependencies** - Only add if truly needed

## Architecture

- `audio/` - VAD recording (don't touch unless audio issues)
- `transcription/` - Provider implementations:
  - `whisper.py` - Local Whisper (openai-whisper, not transformers!)
  - `gemini.py` - Gemini API wrapper (legacy structure)
  - `mistral_api/` - Mistral API wrapper (NEW pattern: subfolder with tests)
  - Future providers follow `mistral_api/` pattern (subfolder + co-located tests)
- `config/` - Settings, model paths
- `test_fixtures/` - Sample audio for integration tests

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

1. **Integration tests** - Do real APIs still work?
   ```bash
   make test  # Must pass before releasing
   ```

2. **Import test** - Does it import without crashing?
   ```bash
   python -c "from otis_scribe_engine import get_transcriber, AudioRecorder"
   ```

3. **App test** - Do client apps still work?
   ```bash
   cd ../otis-dictation-macos-app
   python app.py
   # Record and verify transcription works
   ```

## What NOT to Do

- ❌ Add transformers dependency back
- ❌ Write verbose documentation
- ❌ Add mocked tests (use real integration tests only)
- ❌ Make README longer than code
- ❌ Add complexity without reason
- ❌ Ship releases without running `make test`
