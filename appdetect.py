"""
Display Manager — App-Aware Detection Engine
Detects running games and mapped applications to auto-switch profiles.

Detection layers (GPU-vendor independent):
1. Windows GameConfigStore — OS-level game registry (auto-populated)
2. Steam/Epic/GOG library scan — identifies installed game executables
3. Fullscreen + borderless detection — catches unknown games
4. DirectX/Vulkan DLL check — confirms rendering API usage
5. User-defined app rules — manual exe-to-profile mapping
"""

import os
import ctypes
import ctypes.wintypes
import threading
import time
import winreg

import psutil


# ============================================================
# Known Games Database (built from multiple sources)
# ============================================================

_known_game_exes = set()  # lowercase full paths
_known_games_lock = threading.Lock()
_games_scanned = False


def _scan_gameconfigstore():
    """Read Windows GameConfigStore — the OS already knows what's a game."""
    games = set()
    base = r"System\GameConfigStore\Children"
    try:
        root = winreg.OpenKey(winreg.HKEY_CURRENT_USER, base)
        i = 0
        while True:
            try:
                child_name = winreg.EnumKey(root, i)
                child = winreg.OpenKey(root, child_name)
                try:
                    path, _ = winreg.QueryValueEx(child, "MatchedExeFullPath")
                    games.add(path.lower())
                except FileNotFoundError:
                    pass
                winreg.CloseKey(child)
                i += 1
            except OSError:
                break
        winreg.CloseKey(root)
    except (FileNotFoundError, OSError):
        pass
    return games


def _scan_steam_library():
    """Parse Steam library for installed game executables."""
    games = set()
    try:
        import vdf
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam")
        steam_path, _ = winreg.QueryValueEx(key, "SteamPath")
        winreg.CloseKey(key)

        vdf_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
        if not os.path.exists(vdf_path):
            return games
        with open(vdf_path, "r") as f:
            data = vdf.load(f)

        folders = []
        for k, v in data.get("libraryfolders", {}).items():
            if k.isdigit() and "path" in v:
                folders.append(v["path"])

        for folder in folders:
            steamapps = os.path.join(folder, "steamapps")
            if not os.path.isdir(steamapps):
                continue
            for filename in os.listdir(steamapps):
                if filename.startswith("appmanifest_") and filename.endswith(".acf"):
                    try:
                        acf_path = os.path.join(steamapps, filename)
                        with open(acf_path, "r", encoding="utf-8", errors="ignore") as f:
                            manifest = vdf.load(f)
                        app_state = manifest.get("AppState", {})
                        installdir = app_state.get("installdir", "")
                        if installdir:
                            game_dir = os.path.join(steamapps, "common", installdir)
                            if os.path.isdir(game_dir):
                                # Add all exe files in the game directory (top level)
                                for item in os.listdir(game_dir):
                                    if item.lower().endswith(".exe"):
                                        games.add(os.path.join(game_dir, item).lower())
                    except Exception:
                        pass
    except Exception:
        pass
    return games


def _scan_epic_library():
    """Parse Epic Games Store manifests for installed games."""
    games = set()
    import json
    manifest_dir = os.path.join(
        os.environ.get("ProgramData", r"C:\ProgramData"),
        "Epic", "EpicGamesLauncher", "Data", "Manifests"
    )
    if not os.path.isdir(manifest_dir):
        return games
    try:
        for filename in os.listdir(manifest_dir):
            if filename.endswith(".item"):
                filepath = os.path.join(manifest_dir, filename)
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                install_loc = data.get("InstallLocation", "")
                exe = data.get("LaunchExecutable", "")
                if install_loc and exe:
                    full_path = os.path.join(install_loc, exe)
                    games.add(full_path.lower())
    except Exception:
        pass
    return games


def build_known_games():
    """Scan all sources and build the known games database."""
    global _known_game_exes, _games_scanned
    with _known_games_lock:
        all_games = set()
        all_games.update(_scan_gameconfigstore())
        all_games.update(_scan_steam_library())
        all_games.update(_scan_epic_library())
        _known_game_exes = all_games
        _games_scanned = True
    return len(all_games)


def is_known_game(exe_path):
    """Check if an exe path is a known game."""
    if not _games_scanned:
        build_known_games()
    with _known_games_lock:
        return exe_path.lower() in _known_game_exes


# ============================================================
# Fullscreen Detection (GPU-independent)
# ============================================================

_user32 = ctypes.WinDLL("user32", use_last_error=True)


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.wintypes.DWORD),
        ("rcMonitor", ctypes.wintypes.RECT),
        ("rcWork", ctypes.wintypes.RECT),
        ("dwFlags", ctypes.wintypes.DWORD),
    ]


def is_foreground_fullscreen():
    """Check if the foreground window is fullscreen and borderless.
    Returns (is_fullscreen, pid) or (False, None)."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return False, None

    rect = ctypes.wintypes.RECT()
    _user32.GetWindowRect(hwnd, ctypes.byref(rect))

    monitor = _user32.MonitorFromWindow(hwnd, 2)  # MONITOR_DEFAULTTONEAREST
    mi = MONITORINFO()
    mi.cbSize = ctypes.sizeof(MONITORINFO)
    _user32.GetMonitorInfoW(monitor, ctypes.byref(mi))

    screen = mi.rcMonitor
    is_fs = (rect.left <= screen.left and
             rect.top <= screen.top and
             rect.right >= screen.right and
             rect.bottom >= screen.bottom)

    # Check if window lacks title bar (not just maximised)
    GWL_STYLE = -16
    WS_CAPTION = 0x00C00000
    style = _user32.GetWindowLongW(hwnd, GWL_STYLE)
    no_border = not (style & WS_CAPTION)

    if is_fs and no_border:
        pid = ctypes.wintypes.DWORD()
        _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return True, pid.value

    return False, None


# ============================================================
# DirectX/Vulkan DLL Detection
# ============================================================

GAME_RENDER_DLLS = {"d3d9.dll", "d3d11.dll", "d3d12.dll", "vulkan-1.dll"}
# dxgi.dll excluded — too many non-game apps load it (browsers, etc.)


def process_uses_game_rendering(pid):
    """Check if a process has game rendering DLLs loaded."""
    try:
        proc = psutil.Process(pid)
        for mmap in proc.memory_maps(grouped=False):
            dll_name = os.path.basename(mmap.path).lower()
            if dll_name in GAME_RENDER_DLLS:
                return True
    except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess):
        pass
    return False


# ============================================================
# Foreground App Detection
# ============================================================

def get_foreground_exe():
    """Get the executable path of the current foreground window process."""
    hwnd = _user32.GetForegroundWindow()
    if not hwnd:
        return None
    pid = ctypes.wintypes.DWORD()
    _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value == 0:
        return None
    try:
        proc = psutil.Process(pid.value)
        return proc.exe()
    except (psutil.AccessDenied, psutil.NoSuchProcess):
        return None


# ============================================================
# App Detection Manager
# ============================================================

class AppDetector:
    """Monitors the foreground app and triggers profile switches."""

    def __init__(self, config, profile_manager):
        self.config = config
        self.pm = profile_manager
        self._stop_event = threading.Event()
        self._thread = None
        self._previous_exe = None
        self._pre_app_profile = None  # profile before app-aware switched

    def start(self):
        """Start the detection thread."""
        self._stop_event.clear()
        # Build game database in background
        threading.Thread(target=build_known_games, daemon=True).start()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()

    def reload(self):
        """Rebuild game database (e.g., after new game installed)."""
        threading.Thread(target=build_known_games, daemon=True).start()

    def _get_app_rules(self):
        """Get user-defined app-to-profile rules from config."""
        return self.config.get("app_rules", [])

    def _check_user_rules(self, exe_path):
        """Check if the foreground exe matches a user-defined rule.
        Returns profile name or None."""
        if not exe_path:
            return None
        exe_lower = exe_path.lower()
        exe_name = os.path.basename(exe_lower)
        for rule in self._get_app_rules():
            match = rule.get("exe", "").lower()
            profile = rule.get("profile", "")
            if match and profile:
                # Match by full path or just exe name
                if match in exe_lower or match == exe_name:
                    return profile
        return None

    def _detect_game(self, exe_path):
        """Detect if the foreground app is a game using layered detection.
        Returns True if it's a game."""
        if not exe_path:
            return False

        # Layer 1: Known game database (fastest check)
        if is_known_game(exe_path):
            return True

        # Layer 2: Fullscreen + borderless + rendering DLLs
        is_fs, pid = is_foreground_fullscreen()
        if is_fs and pid:
            if process_uses_game_rendering(pid):
                return True

        return False

    def _run_loop(self):
        """Poll foreground app every 3 seconds."""
        while not self._stop_event.is_set():
            self._stop_event.wait(3)
            if self._stop_event.is_set():
                break

            if not self.config.get("app_aware_enabled", False):
                continue

            exe_path = get_foreground_exe()
            if exe_path == self._previous_exe:
                continue
            self._previous_exe = exe_path

            if not exe_path:
                continue

            # Check user rules first (highest priority)
            user_profile = self._check_user_rules(exe_path)
            if user_profile:
                if self.pm.get_active() != user_profile:
                    if self._pre_app_profile is None:
                        self._pre_app_profile = self.pm.get_active()
                    self._app_switch(user_profile)
                continue

            # Check game detection
            if self._detect_game(exe_path):
                game_profile = self.config.get("game_detect_profile", "Game")
                if self.pm.get_active() != game_profile:
                    if self._pre_app_profile is None:
                        self._pre_app_profile = self.pm.get_active()
                    self._app_switch(game_profile)
                continue

            # No match — revert to previous profile if we auto-switched
            if self._pre_app_profile is not None:
                revert_to = self._pre_app_profile
                self._pre_app_profile = None
                self._app_switch(revert_to)

    def _app_switch(self, profile_name):
        """Switch profile for app detection — bypasses lock without setting lock."""
        profile = self.pm.config.get_profile(profile_name)
        if profile is None:
            return
        import display
        brightness = profile.get("brightness", 70)
        colour_temp = profile.get("colour_temp", 6500)
        refresh_rate = profile.get("refresh_rate", 0)
        transition_ms = self.pm.config.get("transition_ms", 0)

        if display.is_dimmed():
            display.toggle_quick_dim()

        display.apply_profile(brightness, colour_temp, transition_ms)

        if refresh_rate > 0:
            current_rate = display.get_refresh_rate()
            if current_rate != refresh_rate:
                display.set_refresh_rate(refresh_rate)

        self.pm.config.set_active_profile(profile_name)
        if self.pm.on_switch:
            try:
                self.pm.on_switch(profile_name)
            except Exception:
                pass
