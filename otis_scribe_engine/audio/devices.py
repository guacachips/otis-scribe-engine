import sounddevice as sd
from typing import Dict, List, Tuple, Optional

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
