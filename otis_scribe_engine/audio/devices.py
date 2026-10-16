import sounddevice as sd
from typing import Dict, List, Tuple, Optional, Union
from .coreaudio import get_default_input_device_name

class AudioDeviceManager:
    """Manages audio device discovery and selection"""

    @staticmethod
    def list_devices() -> List[Dict]:
        """
        Get a list of all available audio devices

        Returns:
            List[Dict]: List of device information dictionaries
        """
        return sd.query_devices()

    @staticmethod
    def get_default_devices() -> Tuple[int, int]:
        """
        Get the default input and output device IDs

        Returns:
            Tuple[int, int]: (default_input_id, default_output_id)
        """
        return sd.default.device

    @staticmethod
    def refresh() -> None:
        """
        Re-initialize PortAudio so it sees devices plugged in and default changes since import.

        Pa_Terminate closes every open stream: only call this when no stream is active.
        """
        # PortAudio's CoreAudio backend reads the device list and default input only in
        # Pa_Initialize and never listens for changes, so a long-running process keeps
        # recording from whatever was the default at launch. sounddevice exposes no public
        # re-init, hence its private helpers.
        if sd._initialized:
            sd._terminate()
        sd._initialize()

    @staticmethod
    def get_system_default_input_name() -> Optional[str]:
        """Current macOS default input device name (live, unlike PortAudio's default)"""
        return get_default_input_device_name()

    @staticmethod
    def list_input_device_names() -> List[str]:
        """Unique names of devices that can record, in PortAudio order"""
        names = [dev['name'] for dev in sd.query_devices() if dev['max_input_channels'] > 0]
        return list(dict.fromkeys(names))

    @staticmethod
    def find_input_device(name: str) -> Optional[int]:
        """
        Find an input device by name: exact match first, then sounddevice's substring matching

        Returns:
            Optional[int]: Device ID, or None if no single device matches
        """
        for device_id, dev in enumerate(sd.query_devices()):
            if dev['name'] == name and dev['max_input_channels'] > 0:
                return device_id
        # Private sounddevice helper: the same name matching sd.InputStream(device=str) uses.
        device_id = sd._get_device_id(name, 'input')
        return device_id if device_id >= 0 else None

    @staticmethod
    def get_device_info(device_id: int) -> Optional[Dict]:
        """
        Get detailed information about a specific device

        Args:
            device_id (int): The ID of the device to query

        Returns:
            Optional[Dict]: Device information or None if device not found
        """
        try:
            return sd.query_devices(device_id)
        except sd.PortAudioError:
            return None

    @classmethod
    def validate_device(cls, device_id: int) -> Tuple[bool, str, Optional[Dict]]:
        """
        Validate if a device is suitable for recording

        Args:
            device_id (int): The ID of the device to validate

        Returns:
            Tuple[bool, str, Optional[Dict]]:
                - Success status
                - Message describing the result
                - Device info if successful, None otherwise
        """
        device_info = cls.get_device_info(device_id)

        if device_info is None:
            return False, "Device not found", None

        if device_info['max_input_channels'] < 1:
            return False, "Device does not support input", None

        return True, "Device is valid for recording", device_info

    @classmethod
    def resolve_input_device(cls, preference: Union[int, str, None] = None) -> Tuple[int, Dict, str]:
        """
        Pick the input device to open for a preference (device ID, device name, or None for the system default)

        Returns:
            Tuple[int, Dict, str]: Device ID, device info, and where the choice came from

        Raises:
            ValueError: If the resolved device cannot record
        """
        device_id = None
        source = None

        if isinstance(preference, str):
            device_id = cls.find_input_device(preference)
            if device_id is None:
                print(f"\n⚠️  Preferred input device '{preference}' not found, falling back to the system default")
            else:
                source = f"preference '{preference}'"
        elif preference is not None:
            device_id = preference
            source = "device ID preference"

        if device_id is None:
            system_default = cls.get_system_default_input_name()
            if system_default:
                device_id = cls.find_input_device(system_default)
                source = "macOS default"
            if device_id is None:
                device_id = cls.get_default_devices()[0]
                source = "PortAudio default"

        valid, message, device_info = cls.validate_device(device_id)
        if not valid:
            raise ValueError(f"Invalid audio device {device_id}: {message}")
        return device_id, device_info, source

    @classmethod
    def print_device_list(cls) -> int:
        """
        Print a formatted list of all audio devices and return default input device ID

        Returns:
            int: Default input device ID
        """
        default_input, _ = cls.get_default_devices()
        devices = cls.list_devices()

        print("\nAvailable audio devices:")
        for i, dev in enumerate(devices):
            default_marker = " (DEFAULT)" if i == default_input else ""
            print(f"{i}: {dev['name']}{default_marker} "
                  f"(in: {dev['max_input_channels']}, "
                  f"out: {dev['max_output_channels']})")

        return default_input
