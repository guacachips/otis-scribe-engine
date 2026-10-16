import os
from pathlib import Path
import pytest
from .local_server import LocalServerTranscriber, LocalServerUnavailableError, DEFAULT_BASE_URL, DEFAULT_MODEL

# Overrides for running against a server on another port or with a faster model (e.g. whisper-tiny).
BASE_URL = os.getenv("OTIS_SPEECH_SERVER_URL", DEFAULT_BASE_URL)
MODEL = os.getenv("OTIS_SPEECH_SERVER_MODEL", DEFAULT_MODEL)


def test_local_server_integration():
    """Integration test - verifies a running otis-speech-server transcribes real audio"""

    test_fixture = Path(__file__).parent.parent.parent.parent / "test_fixtures" / "sample.wav"

    if not test_fixture.exists():
        pytest.skip(f"Test fixture not found: {test_fixture}")

    transcriber = LocalServerTranscriber(base_url=BASE_URL, model=MODEL, debug=True)
    try:
        transcriber.status()
    except LocalServerUnavailableError:
        pytest.skip(f"otis-speech-server not running at {BASE_URL} (start it with: otis-speech-server)")

    result = transcriber.transcribe(str(test_fixture))

    # Verify contract - what library users depend on
    assert 'text' in result, "Result must contain 'text' key"
    assert 'transcription_time' in result, "Result must contain 'transcription_time' key"
    assert 'model' in result, "Result must contain 'model' key"

    assert isinstance(result['text'], str), "'text' must be a string"
    assert result['text'], "'text' must not be empty for a speech sample"
    assert isinstance(result['transcription_time'], float), "'transcription_time' must be a float"
    assert result['transcription_time'] > 0, "'transcription_time' must be positive"
    assert result['model'] == MODEL, f"Expected model '{MODEL}', got '{result['model']}'"

    # Server errors reach the caller as RuntimeError with the server's message
    with pytest.raises(RuntimeError, match="404"):
        LocalServerTranscriber(base_url=BASE_URL, model="no-such-model").transcribe(str(test_fixture))

    print(f"\n✓ Local server integration test passed")
    print(f"  Transcribed: {result['text'][:50]}...")
    print(f"  Time: {result['transcription_time']:.2f}s")
