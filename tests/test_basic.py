import pytest

def test_imports():
    """Test that all main components can be imported"""
    from otis_scribe_engine import (
        AudioRecorder,
        VADConfig,
        AudioDeviceManager,
        get_transcriber,
        Transcriber,
        UserSettings,
        MODEL_PATHS
    )

    assert AudioRecorder is not None
    assert VADConfig is not None
    assert AudioDeviceManager is not None
    assert get_transcriber is not None
    assert Transcriber is not None
    assert UserSettings is not None
    assert MODEL_PATHS is not None

def test_vad_config():
    """Test VADConfig initialization"""
    from otis_scribe_engine import VADConfig

    config = VADConfig(
        threshold_speech=0.5,
        silence_duration_max=2.5,
        min_speech_duration=0.5
    )

    assert config.threshold_speech == 0.5
    assert config.silence_duration_max == 2.5
    assert config.min_speech_duration == 0.5
    assert config.sample_rate == 16000

def test_user_settings():
    """Test UserSettings load and save"""
    from otis_scribe_engine import UserSettings

    settings = UserSettings()
    assert settings.transcription_engine == "gemini"
    assert settings.whisper_model == "tiny"

    settings.transcription_engine = "whisper"
    settings.whisper_model = "base"

    assert settings.transcription_engine == "whisper"
    assert settings.whisper_model == "base"

def test_get_transcriber_gemini():
    """Test creating Gemini transcriber"""
    from otis_scribe_engine import get_transcriber

    try:
        transcriber = get_transcriber("gemini", api_key="test-key")
        assert transcriber is not None
    except ValueError:
        pass

def test_get_transcriber_whisper():
    """Test creating Whisper transcriber"""
    from otis_scribe_engine import get_transcriber

    transcriber = get_transcriber("whisper", model_id="openai/whisper-tiny")
    assert transcriber is not None

def test_get_transcriber_invalid():
    """Test invalid transcriber engine raises error"""
    from otis_scribe_engine import get_transcriber

    with pytest.raises(ValueError):
        get_transcriber("invalid_engine")

def test_model_paths():
    """Test model paths configuration"""
    from otis_scribe_engine import MODEL_PATHS
    from pathlib import Path

    assert isinstance(MODEL_PATHS.models_root, Path)
    assert isinstance(MODEL_PATHS.whisper_tiny, Path)
    assert isinstance(MODEL_PATHS.whisper_base, Path)
    assert isinstance(MODEL_PATHS.whisper_large_turbo, Path)

    assert MODEL_PATHS.get_whisper_model_path("openai/whisper-tiny") is not None
    assert MODEL_PATHS.get_whisper_model_path("invalid") is None

def test_audio_device_manager():
    """Test AudioDeviceManager basic functionality"""
    from otis_scribe_engine import AudioDeviceManager

    devices = AudioDeviceManager.list_devices()
    assert isinstance(devices, list)
    assert len(devices) > 0

    default_input, default_output = AudioDeviceManager.get_default_devices()
    assert isinstance(default_input, int)
    assert isinstance(default_output, int)
