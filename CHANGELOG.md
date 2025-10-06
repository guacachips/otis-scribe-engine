# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
