.PHONY: test install

test:
	python -m pytest otis_scribe_engine/transcription/ -v -s

install:
	pip install -e ".[all]"
