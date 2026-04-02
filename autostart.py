"""
Display Manager — Windows Auto-Start
Manages the registry Run key for starting with Windows.
"""

import sys
import winreg
from pathlib import Path

APP_NAME = "DisplayManager"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path():
    """Get the command to launch this app."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller exe
        return f'"{sys.executable}"'
    else:
        # Running from source
        main_py = Path(__file__).parent / "main.py"
        return f'"{sys.executable}" "{main_py}"'


def is_autostart_enabled():
    """Check if auto-start is registered."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except OSError:
        return False


def enable_autostart():
    """Register the app to start with Windows."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_exe_path())
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def disable_autostart():
    """Remove the app from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE)
        try:
            winreg.DeleteValue(key, APP_NAME)
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def sync_autostart(config):
    """Sync registry state with config setting."""
    should_autostart = config.get("auto_start", False)
    if should_autostart:
        enable_autostart()
    else:
        disable_autostart()
