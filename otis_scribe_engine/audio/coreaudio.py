"""Live macOS default input device lookup via CoreAudio (ctypes, no extra dependency).

PortAudio snapshots the default input device when it initializes, so it cannot tell us
which microphone macOS considers the default right now. CoreAudio can.
"""
import ctypes
import struct
import sys
from functools import lru_cache
from typing import Optional, Tuple


def _fourcc(code: str) -> int:
    return struct.unpack('>I', code.encode('ascii'))[0]


class _AudioObjectPropertyAddress(ctypes.Structure):
    _fields_ = [
        ('mSelector', ctypes.c_uint32),
        ('mScope', ctypes.c_uint32),
        ('mElement', ctypes.c_uint32),
    ]


_SYSTEM_OBJECT = 1
_UNKNOWN_OBJECT = 0
_DEFAULT_INPUT_DEVICE = _fourcc('dIn ')
_OBJECT_NAME = _fourcc('lnam')
_SCOPE_GLOBAL = _fourcc('glob')
_ELEMENT_MAIN = 0
_UTF8 = 0x08000100


@lru_cache(maxsize=1)
def _frameworks():
    core_audio = ctypes.CDLL('/System/Library/Frameworks/CoreAudio.framework/CoreAudio')
    core_foundation = ctypes.CDLL('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')

    get_property = core_audio.AudioObjectGetPropertyData
    get_property.argtypes = [
        ctypes.c_uint32, ctypes.POINTER(_AudioObjectPropertyAddress),
        ctypes.c_uint32, ctypes.c_void_p,
        ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p,
    ]
    get_property.restype = ctypes.c_int32

    core_foundation.CFStringGetLength.argtypes = [ctypes.c_void_p]
    core_foundation.CFStringGetLength.restype = ctypes.c_long
    core_foundation.CFStringGetMaximumSizeForEncoding.argtypes = [ctypes.c_long, ctypes.c_uint32]
    core_foundation.CFStringGetMaximumSizeForEncoding.restype = ctypes.c_long
    core_foundation.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]
    core_foundation.CFStringGetCString.restype = ctypes.c_bool
    core_foundation.CFRelease.argtypes = [ctypes.c_void_p]
    core_foundation.CFRelease.restype = None

    return get_property, core_foundation


def _describe_status(status: int) -> str:
    code = struct.pack('>i', status)
    if all(32 <= byte < 127 for byte in code):
        return f"{status} ('{code.decode('ascii')}')"
    return str(status)


def _query_default_input_device() -> Tuple[Optional[str], Optional[str]]:
    get_property, cf = _frameworks()

    address = _AudioObjectPropertyAddress(_DEFAULT_INPUT_DEVICE, _SCOPE_GLOBAL, _ELEMENT_MAIN)
    device_id = ctypes.c_uint32(_UNKNOWN_OBJECT)
    size = ctypes.c_uint32(ctypes.sizeof(device_id))
    status = get_property(_SYSTEM_OBJECT, ctypes.byref(address), 0, None,
                          ctypes.byref(size), ctypes.byref(device_id))
    if status != 0:
        return None, f"default input query failed: status={_describe_status(status)}"
    if device_id.value == _UNKNOWN_OBJECT:
        return None, "no default input device"

    address.mSelector = _OBJECT_NAME
    cf_name = ctypes.c_void_p()
    size = ctypes.c_uint32(ctypes.sizeof(cf_name))
    status = get_property(device_id.value, ctypes.byref(address), 0, None,
                          ctypes.byref(size), ctypes.byref(cf_name))
    if status != 0 or not cf_name.value:
        return None, f"name query for device {device_id.value} failed: status={_describe_status(status)}"

    # kAudioObjectPropertyName hands us an owned CFString: we must release it.
    try:
        buffer_size = cf.CFStringGetMaximumSizeForEncoding(cf.CFStringGetLength(cf_name), _UTF8) + 1
        buffer = ctypes.create_string_buffer(buffer_size)
        if not cf.CFStringGetCString(cf_name, buffer, buffer_size, _UTF8):
            return None, f"name of device {device_id.value} is not convertible to UTF-8"
        return buffer.value.decode('utf-8'), None
    finally:
        cf.CFRelease(cf_name)


def query_default_input_device() -> Tuple[Optional[str], Optional[str]]:
    """
    Current macOS default input device. Never raises.

    Returns:
        Tuple[Optional[str], Optional[str]]: (device name, None) on success, (None, failure reason) otherwise
    """
    if sys.platform != 'darwin':
        return None, "not macOS"
    try:
        return _query_default_input_device()
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def get_default_input_device_name() -> Optional[str]:
    """Name of the current macOS default input device, or None if it cannot be determined."""
    return query_default_input_device()[0]
