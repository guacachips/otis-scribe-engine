import time
from pathlib import Path
from typing import Dict, Callable, Optional
from huggingface_hub import snapshot_download
from ..config.model_paths import MODEL_PATHS

def format_size(bytes_size: int) -> str:
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"

def get_directory_size(path: Path) -> int:
    """Get total size of directory in bytes"""
    return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())

class ModelDownloader:
    """Handles downloading and caching of Whisper models locally"""

    def __init__(self):
        self.model_paths = MODEL_PATHS
        self.downloaded_models = []
        self.failed_models = []

    def download_whisper_models(self, progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Download all Whisper models

        Args:
            progress_callback: Optional callback function(model_name: str, status: str)

        Returns:
            Dict[str, bool]: Map of model_id to success status
        """
        whisper_models = {
            "openai/whisper-tiny": self.model_paths.whisper_tiny,
            "openai/whisper-base": self.model_paths.whisper_base,
            "openai/whisper-large-v3-turbo": self.model_paths.whisper_large_turbo,
        }

        results = {}

        for model_id, local_path in whisper_models.items():
            print(f"\n{'='*60}")
            print(f"Downloading Whisper model: {model_id}")
            print(f"Target location: {local_path}")

            if progress_callback:
                progress_callback(model_id, "checking")

            if self.model_paths.model_exists(local_path):
                print(f"✓ Model already exists, skipping download")
                results[model_id] = True
                if progress_callback:
                    progress_callback(model_id, "exists")
                continue

            try:
                start_time = time.time()

                local_path.mkdir(parents=True, exist_ok=True)

                if progress_callback:
                    progress_callback(model_id, "downloading")

                snapshot_download(
                    repo_id=model_id,
                    local_dir=str(local_path),
                    local_dir_use_symlinks=False,
                    resume_download=True,
                )

                download_time = time.time() - start_time
                model_size = get_directory_size(local_path)

                print(f"✓ Successfully downloaded {model_id}")
                print(f"  Size: {format_size(model_size)}")
                print(f"  Time: {download_time:.1f}s")

                self.downloaded_models.append(model_id)
                results[model_id] = True

                if progress_callback:
                    progress_callback(model_id, "completed")

            except Exception as e:
                print(f"✗ Failed to download {model_id}: {e}")
                self.failed_models.append(model_id)
                results[model_id] = False

                if progress_callback:
                    progress_callback(model_id, "failed")

        return results

    def download_all_models(self, progress_callback: Optional[Callable] = None) -> Dict[str, bool]:
        """Download all Whisper models

        Args:
            progress_callback: Optional callback function(model_name: str, status: str)

        Returns:
            Dict[str, bool]: Map of model_id to success status
        """
        print("Starting download of Whisper models for offline operation...")
        print(f"Models will be stored in: {self.model_paths.models_root}")

        self.model_paths.create_directories()

        print(f"\n{'#'*60}")
        print("DOWNLOADING WHISPER MODELS")
        print(f"{'#'*60}")
        results = self.download_whisper_models(progress_callback)

        self.print_summary(results)

        return results

    def print_summary(self, results: Dict[str, bool]):
        """Print download summary"""
        print(f"\n{'='*60}")
        print("DOWNLOAD SUMMARY")
        print(f"{'='*60}")

        total_successful = sum(1 for success in results.values() if success)
        total_failed = sum(1 for success in results.values() if not success)

        print(f"\nWhisper Models:")
        for model, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {model}")

        print(f"\nOverall Results:")
        print(f"  ✓ Successful: {total_successful}")
        print(f"  ✗ Failed: {total_failed}")

        if total_failed == 0:
            print("\n🎉 All models are ready for offline operation!")
        else:
            print(f"\n⚠️  {total_failed} models need attention before full offline operation")

        if self.model_paths.models_root.exists():
            total_size = get_directory_size(self.model_paths.models_root)
            print(f"\nTotal disk usage: {format_size(total_size)}")

def main():
    """Main function for direct script usage"""
    import sys

    auto_mode = '--auto' in sys.argv or '-y' in sys.argv

    downloader = ModelDownloader()

    print("Otis Scribe Engine - Model Downloader")
    print("This will download Whisper models for offline operation")
    print("This may take several minutes and require significant disk space")

    if not auto_mode:
        try:
            response = input("\nProceed with download? (y/N): ").strip().lower()
            if response != 'y':
                print("Download cancelled")
                return
        except (EOFError, KeyboardInterrupt):
            print("\nDownload cancelled")
            return
    else:
        print("\n[AUTO MODE] Proceeding with download automatically...")

    results = downloader.download_all_models()

    all_successful = all(results.values())

    if all_successful:
        print("\n🚀 System is ready for completely offline operation!")
    else:
        print("\n📋 Some models are missing. Check the summary above.")
        print("The system will work but may require internet for missing models.")

if __name__ == "__main__":
    main()
