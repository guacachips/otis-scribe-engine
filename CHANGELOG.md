# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-10-23

### Added
- `LocalServerLiveTranscriber(base_url, model="voxtral-realtime-4bit", transcription_delay_ms=480, on_delta, on_error, on_final, chunk_ms=320)`: live transcription over the `otis-speech-server` WebSocket endpoint `/v1/audio/transcriptions/realtime` (requires otis-speech-server 0.2.0 or later). `start()`, `feed(samples)` (never blocks; audio is dropped and counted in `dropped_seconds` if the sender falls behind), `finish(timeout)` returning `{'text', 'transcription_time', 'model', 'stats'}`, `cancel()` and the `text` property. `on_delta(delta, text_so_far)` streams text as it arrives; `on_final(stop_reason)` signals a session the server ended itself (`eos`, `max_duration`)
- Failures raise `RuntimeError` carrying `.code` (the server error code, e.g. `busy`, `model_not_found`) and `.partial_text`; `start()` raises `LocalServerUnavailableError` when the server is not reachable. No reconnect
- `AudioRecorder(on_audio=...)` receives each captured block (float32 mono 16 kHz) as it is recorded. Live audio is sent un-normalized; the saved WAV is still peak-normalized
- Live integration tests (skip when no server is running)

### Changed
- `websockets>=15` is now a direct dependency (it was only installed through google-genai)

### Fixed
- A `stop_recording()` issued while `record()` was starting could be lost, leaving the recording running

## [0.4.0] - 2026-10-16

### Added
- `local-server` engine: `LocalServerTranscriber(base_url="http://127.0.0.1:6847", model="voxtral-realtime-4bit", language=None, timeout=600)` transcribes through a running `otis-speech-server` (local MLX Voxtral/Whisper models) over its OpenAI-style `/v1/audio/transcriptions` endpoint, using only the standard library
- `LocalServerUnavailableError` (a `ConnectionError`) when the server is not reachable, with the command to start it; server errors are raised as `RuntimeError` carrying the server's message
- Integration test that skips when no server is running (`OTIS_SPEECH_SERVER_URL` / `OTIS_SPEECH_SERVER_MODEL` override address and model)

## [0.3.2] - 2026-10-16

### Added
- `AudioRecorder(device_id=...)` accepts a device name (resolved at each `record()`, falls back to the macOS default if missing)
- `DeadInputError` raised when the input device delivers only zeros (after one retry), instead of saving a silent file
- `DeadInputError` also raised when the input device delivers no audio at all for 3 s (previously the recording hung forever)
- Live macOS default input lookup via CoreAudio, and one diagnostic line per recording (macOS default or the CoreAudio failure status, PortAudio default, device opened)
- `AudioDeviceManager.refresh()`, `stream_open()`, `list_input_device_names()`, `resolve_input_device()`; device queries and re-init share a lock, and `refresh()` refuses to run while a stream is open

### Fixed
- Recording from a stale microphone: PortAudio froze the default input at import, so a long-running app ignored later default changes. PortAudio is now re-initialized before each recording
- `device_id=0` was silently replaced by the default device
- Manual stop saved the recording twice; `stop_recording()` now only stops and `record()` saves
- `__version__` now matches the package version

## [0.3.1] - 2025-10-06

### Added
- Token tracking for Mistral transcriber (debug mode)

### Changed
- Removed cost calculation from Gemini and Mistral transcribers
- Simplified token data structure (only total_tokens returned)

## [0.3.0] - 2025-10-05

### Added
- Mistral API transcription support with Voxtral models (voxtral-mini-latest)
- Integration test strategy with real API tests (no mocks)
- `.env` support for secure API key management
- `Makefile` for easy testing (`make test`, `make install`)
- Development dependencies (`pytest`) for contributors
- Test fixtures with real speech samples
- Comprehensive testing documentation in AGENTS.md

### Changed
- Updated documentation with integration test philosophy
- Improved contribution guidelines in README
- Enhanced AGENTS.md with coding principles and test strategy

## [0.2.2] - 2025-10-05

### Changed
- Updated release process and commit conventions in AGENTS.md

## [0.2.1] - 2025-10-05

### Removed
- Obsolete HuggingFace model download scripts

## [0.2.0] - 2025-10-05

### Changed
- Migrated from transformers to openai-whisper for better performance and compatibility
- Fixed incomplete transcriptions caused by transformers 4.50+ breaking changes

### Added
- torch and torchaudio as base dependencies for VAD support

## [0.1.0] - 2025-10-05

### Added
- Initial release of Otis Scribe Engine
- VAD-based audio recording with Silero VAD
- Whisper transcription (local)
- Gemini API transcription
- Audio device management
- User settings and model paths configuration

[0.3.1]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.3.1
[0.3.0]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.3.0
[0.2.2]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.2.2
[0.2.1]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.2.1
[0.2.0]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.2.0
[0.1.0]: https://github.com/guacachips/otis-scribe-engine/releases/tag/v0.1.0
