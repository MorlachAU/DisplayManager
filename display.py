"""
DisplayPal — Hardware Control
DDC/CI brightness via monitorcontrol + colour temperature via gamma ramp.
"""

import ctypes
import ctypes.wintypes
import math
import time
import threading


# ============================================================
# Gamma Ramp (colour temperature)
# ============================================================

class GAMMA_RAMP(ctypes.Structure):
    _fields_ = [
        ("Red", ctypes.wintypes.WORD * 256),
        ("Green", ctypes.wintypes.WORD * 256),
        ("Blue", ctypes.wintypes.WORD * 256),
    ]


_gdi32 = ctypes.windll.gdi32
_user32 = ctypes.windll.user32

# Track current state for gradual transitions
_current_kelvin = 6500
_kelvin_lock = threading.Lock()


def kelvin_to_rgb(kelvin):
    """Convert colour temperature in Kelvin to RGB multipliers (0.0 - 1.0).
    Uses Tanner Helland algorithm."""
    temp = kelvin / 100.0

    if temp <= 66:
        red = 255
    else:
        red = temp - 60
        red = 329.698727446 * (red ** -0.1332047592)
        red = max(0, min(255, red))

    if temp <= 66:
        green = 99.4708025861 * math.log(temp) - 161.1195681661
        green = max(0, min(255, green))
    else:
        green = temp - 60
        green = 288.1221695283 * (green ** -0.0755148492)
        green = max(0, min(255, green))

    if temp >= 66:
        blue = 255
    elif temp <= 19:
        blue = 0
    else:
        blue = 138.5177312231 * math.log(temp - 10) - 305.0447927307
        blue = max(0, min(255, blue))

    return (red / 255.0, green / 255.0, blue / 255.0)


def _build_gamma_ramp(red_mult, green_mult, blue_mult):
    """Build a gamma ramp with RGB channel multipliers (0.0 - 1.0)."""
    ramp = GAMMA_RAMP()
    for i in range(256):
        identity = i * 256
        ramp.Red[i] = min(65535, int(identity * red_mult))
        ramp.Green[i] = min(65535, int(identity * green_mult))
        ramp.Blue[i] = min(65535, int(identity * blue_mult))
    return ramp


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.wintypes.DWORD),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.wintypes.DWORD),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128),
    ]


def _get_active_displays():
    """Enumerate all active display device names."""
    displays = []
    dd = DISPLAY_DEVICE()
    dd.cb = ctypes.sizeof(DISPLAY_DEVICE)
    i = 0
    while _user32.EnumDisplayDevicesW(None, i, ctypes.byref(dd), 0):
        if dd.StateFlags & 1:  # DISPLAY_DEVICE_ATTACHED_TO_DESKTOP
            displays.append(dd.DeviceName)
        i += 1
    return displays


def _set_gamma_ramp(ramp):
    """Apply a gamma ramp to ALL active displays."""
    displays = _get_active_displays()
    if not displays:
        # Fallback: primary display
        hdc = _user32.GetDC(0)
        result = _gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp))
        _user32.ReleaseDC(0, hdc)
        return bool(result)

    success = False
    for device_name in displays:
        hdc = _gdi32.CreateDCW(device_name, None, None, None)
        if hdc:
            if _gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp)):
                success = True
            _gdi32.DeleteDC(hdc)
    return success


def set_colour_temperature(kelvin):
    """Set display colour temperature in Kelvin (1200 - 6500)."""
    global _current_kelvin
    kelvin = max(1200, min(6500, kelvin))
    r, g, b = kelvin_to_rgb(kelvin)
    ramp = _build_gamma_ramp(r, g, b)
    result = _set_gamma_ramp(ramp)
    if result:
        with _kelvin_lock:
            _current_kelvin = kelvin
        _store_expected_ramp(kelvin)
    return result


def get_colour_temperature():
    """Return the last-set colour temperature."""
    with _kelvin_lock:
        return _current_kelvin


def reset_colour_temperature():
    """Reset to neutral 6500K (identity ramp)."""
    return set_colour_temperature(6500)


# ============================================================
# Brightness via screen_brightness_control (laptop + DDC/CI)
# ============================================================

_cached_displays = None
_monitor_lock = threading.Lock()


def _get_displays():
    """Find and cache all available displays (laptop + external)."""
    global _cached_displays
    with _monitor_lock:
        if _cached_displays is not None:
            return _cached_displays
        try:
            import screen_brightness_control as sbc
            _cached_displays = sbc.list_monitors()
        except Exception:
            _cached_displays = []
        return _cached_displays


def get_monitor_count():
    """Return number of detected displays."""
    return len(_get_displays())


def get_brightness(monitor_index=None):
    """Read current brightness (0-100). Returns None on failure.
    Works on both laptop screens (WMI) and external monitors (DDC/CI)."""
    try:
        import screen_brightness_control as sbc
        displays = _get_displays()
        if not displays:
            return None
        if monitor_index is not None and monitor_index < len(displays):
            result = sbc.get_brightness(display=displays[monitor_index])
        else:
            result = sbc.get_brightness(display=displays[0])
        # sbc returns a list, take first value
        if isinstance(result, list):
            return result[0] if result else None
        return result
    except Exception:
        return None


def set_brightness(value, monitor_index=None):
    """Set brightness (0-100). If monitor_index is None, sets all displays.
    Works on both laptop screens (WMI) and external monitors (DDC/CI)."""
    value = max(0, min(100, value))
    try:
        import screen_brightness_control as sbc
        displays = _get_displays()
        if not displays:
            return False
        if monitor_index is not None:
            if monitor_index < len(displays):
                sbc.set_brightness(value, display=displays[monitor_index])
            else:
                return False
        else:
            for d in displays:
                try:
                    sbc.set_brightness(value, display=d)
                    time.sleep(0.02)
                except Exception:
                    pass
        return True
    except Exception:
        return False


# ============================================================
# Combined profile application
# ============================================================

def nudge_brightness(delta):
    """Adjust brightness by delta (positive or negative). Returns new value or None."""
    current = get_brightness()
    if current is None:
        return None
    new_value = max(0, min(100, current + delta))
    if set_brightness(new_value):
        return new_value
    return None


def nudge_colour_temperature(delta):
    """Adjust colour temperature by delta Kelvin. Returns new value."""
    current = get_colour_temperature()
    new_value = max(1200, min(6500, current + delta))
    if set_colour_temperature(new_value):
        return new_value
    return None


def apply_profile(brightness, colour_temp, transition_ms=0):
    """Apply brightness and colour temperature together.
    If transition_ms > 0, gradually interpolate over that duration."""
    if transition_ms <= 0:
        b_ok = set_brightness(brightness)
        time.sleep(0.05)  # small gap for I2C bus
        c_ok = set_colour_temperature(colour_temp)
        return b_ok and c_ok

    # Gradual transition
    steps = max(5, transition_ms // 100)
    interval = transition_ms / 1000.0 / steps

    start_brightness = get_brightness() or brightness
    start_kelvin = get_colour_temperature()

    for i in range(1, steps + 1):
        t = i / steps
        b = int(start_brightness + (brightness - start_brightness) * t)
        k = int(start_kelvin + (colour_temp - start_kelvin) * t)
        set_brightness(b)
        set_colour_temperature(k)
        time.sleep(interval)

    return True


def check_ddc_available():
    """Check if brightness control is available. Returns (available, message)."""
    displays = _get_displays()
    if not displays:
        return False, "No displays found. Check DDC/CI is enabled in your monitor OSD settings."
    brightness = get_brightness()
    if brightness is not None:
        return True, f"Brightness control working ({len(displays)} display(s)). Current: {brightness}%"
    return False, "Displays detected but brightness control failed."


# ============================================================
# Refresh Rate via Windows Display Settings API
# ============================================================

class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.wintypes.WORD),
        ("dmDriverVersion", ctypes.wintypes.WORD),
        ("dmSize", ctypes.wintypes.WORD),
        ("dmDriverExtra", ctypes.wintypes.WORD),
        ("dmFields", ctypes.wintypes.DWORD),
        ("dmPositionX", ctypes.c_long),
        ("dmPositionY", ctypes.c_long),
        ("dmDisplayOrientation", ctypes.wintypes.DWORD),
        ("dmDisplayFixedOutput", ctypes.wintypes.DWORD),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.wintypes.WORD),
        ("dmBitsPerPel", ctypes.wintypes.DWORD),
        ("dmPelsWidth", ctypes.wintypes.DWORD),
        ("dmPelsHeight", ctypes.wintypes.DWORD),
        ("dmDisplayFlags", ctypes.wintypes.DWORD),
        ("dmDisplayFrequency", ctypes.wintypes.DWORD),
    ]


DM_DISPLAYFREQUENCY = 0x400000
CDS_UPDATEREGISTRY = 0x01
DISP_CHANGE_SUCCESSFUL = 0
ENUM_CURRENT_SETTINGS = -1


def get_refresh_rate():
    """Get current display refresh rate in Hz."""
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    if _user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return dm.dmDisplayFrequency
    return None


def get_available_refresh_rates():
    """Get list of supported refresh rates at current resolution."""
    dm_current = DEVMODE()
    dm_current.dmSize = ctypes.sizeof(DEVMODE)
    _user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm_current))

    rates = set()
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    i = 0
    while _user32.EnumDisplaySettingsW(None, i, ctypes.byref(dm)):
        if (dm.dmPelsWidth == dm_current.dmPelsWidth and
                dm.dmPelsHeight == dm_current.dmPelsHeight and
                dm.dmBitsPerPel == dm_current.dmBitsPerPel):
            rates.add(dm.dmDisplayFrequency)
        i += 1

    return sorted(rates)


def set_refresh_rate(hz):
    """Set display refresh rate. Returns True on success."""
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    if not _user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return False
    dm.dmDisplayFrequency = hz
    dm.dmFields = DM_DISPLAYFREQUENCY
    result = _user32.ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
    return result == DISP_CHANGE_SUCCESSFUL


# ============================================================
# Resolution via Windows Display Settings API
# ============================================================

DM_PELSWIDTH = 0x80000
DM_PELSHEIGHT = 0x100000


def get_resolution():
    """Get current display resolution as (width, height)."""
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    if _user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return (dm.dmPelsWidth, dm.dmPelsHeight)
    return None


def get_available_resolutions(min_height=720):
    """Get list of supported resolutions, filtered to min_height and above."""
    resolutions = set()
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    i = 0
    while _user32.EnumDisplaySettingsW(None, i, ctypes.byref(dm)):
        if dm.dmPelsHeight >= min_height:
            resolutions.add((dm.dmPelsWidth, dm.dmPelsHeight))
        i += 1
    return sorted(resolutions, reverse=True)


def set_resolution(width, height):
    """Set display resolution. Returns True on success."""
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    if not _user32.EnumDisplaySettingsW(None, ENUM_CURRENT_SETTINGS, ctypes.byref(dm)):
        return False
    dm.dmPelsWidth = width
    dm.dmPelsHeight = height
    dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT
    result = _user32.ChangeDisplaySettingsW(ctypes.byref(dm), CDS_UPDATEREGISTRY)
    return result == DISP_CHANGE_SUCCESSFUL


# ============================================================
# Gamma Ramp Watchdog (monitor wake recovery)
# ============================================================

_expected_ramp = None
_expected_ramp_lock = threading.Lock()


def _store_expected_ramp(kelvin):
    """Store what the gamma ramp should be so the watchdog can detect resets."""
    global _expected_ramp
    r, g, b = kelvin_to_rgb(kelvin)
    with _expected_ramp_lock:
        _expected_ramp = (r, g, b)


def check_gamma_ramp_intact():
    """Check if the current gamma ramp matches what we set.
    Returns True if intact, False if it was reset (e.g., after monitor wake)."""
    with _expected_ramp_lock:
        if _expected_ramp is None:
            return True
        r, g, b = _expected_ramp

    # Read current ramp
    hdc = _user32.GetDC(0)
    ramp = GAMMA_RAMP()
    result = _gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp))
    _user32.ReleaseDC(0, hdc)
    if not result:
        return True  # can't read, assume fine

    # Check a few sample points against expected values
    for i in [64, 128, 192]:
        identity = i * 256
        expected_r = min(65535, int(identity * r))
        expected_g = min(65535, int(identity * g))
        expected_b = min(65535, int(identity * b))
        # Allow some tolerance (gamma ramp values can be slightly off)
        if (abs(ramp.Red[i] - expected_r) > 512 or
                abs(ramp.Green[i] - expected_g) > 512 or
                abs(ramp.Blue[i] - expected_b) > 512):
            return False

    return True


# ============================================================
# Quick Dim
# ============================================================

_pre_dim_brightness = None
_is_dimmed = False
_dim_lock = threading.Lock()
QUICK_DIM_LEVEL = 10


def toggle_quick_dim():
    """Toggle between current brightness and dim level. Returns new dimmed state."""
    global _pre_dim_brightness, _is_dimmed
    with _dim_lock:
        if _is_dimmed:
            # Restore
            if _pre_dim_brightness is not None:
                set_brightness(_pre_dim_brightness)
            _is_dimmed = False
            return False
        else:
            # Dim
            _pre_dim_brightness = get_brightness() or 70
            set_brightness(QUICK_DIM_LEVEL)
            _is_dimmed = True
            return True


def is_dimmed():
    with _dim_lock:
        return _is_dimmed


# ============================================================
# Disco Mode (easter egg)
# ============================================================

_disco_running = False
_disco_lock = threading.Lock()


def start_disco(duration=5.0):
    """Rapidly cycle through wild colour temperatures for a few seconds."""
    global _disco_running
    import random

    with _disco_lock:
        if _disco_running:
            return
        _disco_running = True

    def run():
        global _disco_running
        start = time.time()
        temps = [1500, 2000, 3000, 4000, 5500, 6500, 2500, 1800, 3500, 5000]
        i = 0
        while time.time() - start < duration:
            t = temps[i % len(temps)]
            # Add some randomness
            t = max(1200, min(6500, t + random.randint(-500, 500)))
            set_colour_temperature(t)
            time.sleep(0.15)
            i += 1
        with _disco_lock:
            _disco_running = False

    threading.Thread(target=run, daemon=True).start()


def is_disco_running():
    with _disco_lock:
        return _disco_running
