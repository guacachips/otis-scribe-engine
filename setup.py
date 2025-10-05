from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="otis-scribe-engine",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "sounddevice>=0.4.0",
        "soundfile>=0.12.0",
        "scipy>=1.10.0",
        "numpy>=1.24.0",
        "python-dotenv>=1.0.0",
        "torch>=2.0.0",
        "torchaudio>=2.0.0",
    ],
    extras_require={
        "whisper": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "accelerate>=0.20.0",
            "huggingface_hub>=0.16.0",
        ],
        "gemini": [
            "google-genai>=1.0.0",
        ],
        "all": [
            "torch>=2.0.0",
            "transformers>=4.30.0",
            "accelerate>=0.20.0",
            "huggingface_hub>=0.16.0",
            "google-genai>=1.0.0",
        ],
    },
    python_requires=">=3.11",
    author="guacachips",
    description="Voice recording and transcription engine with VAD and multiple backends (Whisper, Gemini)",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/guacachips/otis-scribe-engine",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "Programming Language :: Python :: 3.11",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
    ],
)
