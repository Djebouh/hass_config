"""Scan for parrotpot devices"""

# use only lower case names here
VALID_DEVICE_NAMES = ['Parrot pot']

DEVICE_PREFIX = 'A0:14:3D:CD:'


def scan(backend, timeout=10):
    """Scan for parrotpot devices.

    Note: this must be run as root!
    """
    result = []
    for (mac, name) in backend.scan_for_devices(timeout):
        if (name is not None and name.lower() in VALID_DEVICE_NAMES) or \
                mac is not None and mac.upper().startswith(DEVICE_PREFIX):
            result.append(mac.upper())
    return result
