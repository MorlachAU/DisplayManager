"""
Display Manager — Configuration
Thread-safe JSON config with defaults and deep-merge on load.
"""

import json
import threading
import copy
from pathlib import Path


DEFAULTS = {
    "version": 1,
    "active_profile": "Work",
    "transition_ms": 0,
    "auto_start": True,
    "schedule_enabled": False,
    "first_run_complete": False,
    "quick_dim_hotkey": "ctrl+alt+d",
    "profile_lock": False,
    "ambient_mode": False,
    "notifications_enabled": True,
    "profiles": {
        "Work": {"brightness": 80, "colour_temp": 6500, "hotkey": "ctrl+alt+1", "refresh_rate": 60},
        "Code": {"brightness": 50, "colour_temp": 5000, "hotkey": "ctrl+alt+2", "refresh_rate": 60},
        "Game": {"brightness": 75, "colour_temp": 6500, "hotkey": "ctrl+alt+3", "refresh_rate": 100},
        "Cinema": {"brightness": 30, "colour_temp": 3500, "hotkey": "ctrl+alt+4", "refresh_rate": 0},
    },
    "schedule_rules": [
        {"time": "08:00", "profile": "Work"},
        {"time": "18:00", "profile": "Code"},
    ],
    "sun_schedule": {
        "enabled": False,
        "latitude": 0.0,
        "longitude": 0.0,
        "sunrise_profile": "Work",
        "sunset_profile": "Code",
    },
    "stats": {},
}


class Config:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = Path(__file__).parent
        self._path = Path(config_dir) / "config.json"
        self._lock = threading.Lock()
        self._data = {}
        self.load()

    def load(self):
        """Load config from disk, deep-merging with defaults."""
        with self._lock:
            if self._path.exists():
                try:
                    with open(self._path, "r", encoding="utf-8") as f:
                        loaded = json.load(f)
                    self._data = self._deep_merge(copy.deepcopy(DEFAULTS), loaded)
                except (json.JSONDecodeError, OSError):
                    self._data = copy.deepcopy(DEFAULTS)
            else:
                self._data = copy.deepcopy(DEFAULTS)
            self._save_unlocked()

    def save(self):
        """Save config to disk."""
        with self._lock:
            self._save_unlocked()

    def _save_unlocked(self):
        """Save without acquiring lock (caller must hold lock)."""
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2)

    def get(self, key, default=None):
        """Get a top-level config value."""
        with self._lock:
            return copy.deepcopy(self._data.get(key, default))

    def set(self, key, value):
        """Set a top-level config value and save."""
        with self._lock:
            self._data[key] = value
            self._save_unlocked()

    def get_profile(self, name):
        """Get a profile dict by name. Returns None if not found."""
        with self._lock:
            profiles = self._data.get("profiles", {})
            profile = profiles.get(name)
            return copy.deepcopy(profile) if profile else None

    def set_profile(self, name, profile_data):
        """Update a profile and save."""
        with self._lock:
            if "profiles" not in self._data:
                self._data["profiles"] = {}
            self._data["profiles"][name] = profile_data
            self._save_unlocked()

    def get_all_profiles(self):
        """Return dict of all profiles."""
        with self._lock:
            return copy.deepcopy(self._data.get("profiles", {}))

    def get_active_profile(self):
        """Return the name of the active profile."""
        return self.get("active_profile", "Work")

    def set_active_profile(self, name):
        """Set the active profile name."""
        self.set("active_profile", name)

    def get_schedule_rules(self):
        """Return list of schedule rules."""
        return self.get("schedule_rules", [])

    def set_schedule_rules(self, rules):
        """Set schedule rules and save."""
        self.set("schedule_rules", rules)

    @staticmethod
    def _deep_merge(base, override):
        """Deep-merge override into base. Override values win."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = Config._deep_merge(result[key], value)
            else:
                result[key] = value
        return result
