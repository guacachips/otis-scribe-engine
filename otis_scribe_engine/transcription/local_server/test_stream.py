import os
import time
from math import gcd
from pathlib import Path
import pytest
import soundfile as sf
from scipy.signal import resample_poly
from .local_server import LocalServerTranscriber, LocalServerUnavailableError, DEFAULT_BASE_URL, DEFAULT_MODEL
from .stream import LocalServerLiveTranscriber, SAMPLE_RATE

BASE_URL = os.getenv("OTIS_SPEECH_SERVER_URL", DEFAULT_BASE_URL)
CHUNK_SECONDS = 0.32


@pytest.fixture(scope="module")
def audio_16k():
    test_fixture = Path(__file__).parent.parent.parent.parent / "test_fixtures" / "sample.wav"
    if not test_fixture.exists():
        pytest.skip(f"Test fixture not found: {test_fixture}")
    try:
        LocalServerTranscriber(base_url=BASE_URL).status()
    except LocalServerUnavailableError:
        pytest.skip(f"otis-speech-server not running at {BASE_URL} (start it with: otis-speech-server)")

    audio, rate = sf.read(str(test_fixture), dtype="float32")
    if audio.ndim > 1:
        audio = audio[:, 0]
    g = gcd(SAMPLE_RATE, rate)
    return resample_poly(audio, SAMPLE_RATE // g, rate // g).astype("float32")


def test_local_server_live_integration(audio_16k):
    """Integration test - streams real audio at real-time pace to a running otis-speech-server"""

    deltas = []
    errors = []
    transcriber = LocalServerLiveTranscriber(
        base_url=BASE_URL, model=DEFAULT_MODEL, debug=True,
        on_delta=lambda delta, text_so_far: deltas.append(delta),
        on_error=errors.append,
    )
    transcriber.start()

    chunk = int(SAMPLE_RATE * CHUNK_SECONDS)
    t0 = time.monotonic()
    for i, start in enumerate(range(0, len(audio_16k), chunk)):
        transcriber.feed(audio_16k[start:start + chunk])
        time.sleep(max(0.0, t0 + (i + 1) * CHUNK_SECONDS - time.monotonic()))
    deltas_before_finish = len(deltas)

    result = transcriber.finish()

    # Verify contract - what library users depend on
    for key in ('text', 'transcription_time', 'model', 'stats'):
        assert key in result, f"Result must contain '{key}' key"
    assert isinstance(result['text'], str) and result['text'], "'text' must be a non-empty string"
    assert isinstance(result['transcription_time'], float), "'transcription_time' must be a float"
    assert result['model'] == DEFAULT_MODEL, f"Expected model '{DEFAULT_MODEL}', got '{result['model']}'"
    assert result['stats'].get('stop_reason') == "end", f"Unexpected stats: {result['stats']}"

    assert deltas_before_finish >= 1, "Text must arrive while audio is still being fed"
    assert not errors, f"on_error was called: {errors}"
    assert transcriber.dropped_seconds == 0

    print(f"\n✓ Local server live integration test passed")
    print(f"  Deltas: {len(deltas)} ({deltas_before_finish} before finish), {len(result['text'])} characters")
    print(f"  Finalize: {result['transcription_time']:.2f}s, stats: {result['stats']}")


def test_local_server_live_unknown_model(audio_16k):
    """Server errors reach the caller as RuntimeError carrying the server's error code"""

    errors = []
    transcriber = LocalServerLiveTranscriber(base_url=BASE_URL, model="no-such-model", on_error=errors.append)
    transcriber.start()
    transcriber.feed(audio_16k[:SAMPLE_RATE])

    with pytest.raises(RuntimeError, match="model_not_found"):
        transcriber.finish(timeout=10)
    assert len(errors) == 1 and errors[0].code == "model_not_found"
