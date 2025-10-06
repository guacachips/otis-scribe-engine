import pytest
import os
from pathlib import Path
from dotenv import load_dotenv
from .mistral import MistralTranscriber

# Load .env before test discovery
load_dotenv()


@pytest.mark.skipif(
    not os.getenv("MISTRAL_API_KEY"),
    reason="Set MISTRAL_API_KEY environment variable to run Mistral integration tests"
)
def test_mistral_integration():
    """Integration test - verifies Mistral API actually works with real audio"""

    test_fixture = Path(__file__).parent.parent.parent.parent / "test_fixtures" / "sample.wav"

    if not test_fixture.exists():
        pytest.skip(f"Test fixture not found: {test_fixture}")

    transcriber = MistralTranscriber(debug=True)
    result = transcriber.transcribe(str(test_fixture))

    # Verify contract - what library users depend on
    assert 'text' in result, "Result must contain 'text' key"
    assert 'transcription_time' in result, "Result must contain 'transcription_time' key"
    assert 'model' in result, "Result must contain 'model' key"

    assert isinstance(result['text'], str), "'text' must be a string"
    assert isinstance(result['transcription_time'], float), "'transcription_time' must be a float"
    assert result['transcription_time'] > 0, "'transcription_time' must be positive"
    assert result['model'] == "voxtral-mini-latest", f"Expected model 'voxtral-mini-latest', got '{result['model']}'"

    print(f"\n✓ Mistral integration test passed")
    print(f"  Transcribed: {result['text'][:50]}...")
    print(f"  Time: {result['transcription_time']:.2f}s")
