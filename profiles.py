"""
Display Manager — Profile Management
Switches between named profiles, applying display settings.
"""

import threading
import display


class ProfileManager:
    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self.on_switch = None  # callback(profile_name) — set after construction
        self.on_lock_change = None  # callback(locked: bool) — set after construction

    def switch(self, profile_name, force=False):
        """Switch to a named profile. Returns True on success.
        If profile lock is active and force=False, the switch is blocked."""
        with self._lock:
            # Check profile lock (force bypasses it — used by manual switches)
            if not force and self.config.get("profile_lock", False):
                return False

            profile = self.config.get_profile(profile_name)
            if profile is None:
                return False

            brightness = profile.get("brightness", 70)
            colour_temp = profile.get("colour_temp", 6500)
            refresh_rate = profile.get("refresh_rate", 0)
            transition_ms = self.config.get("transition_ms", 0)

            # Un-dim if dimmed
            if display.is_dimmed():
                display.toggle_quick_dim()

            success = display.apply_profile(brightness, colour_temp, transition_ms)

            # Apply refresh rate if specified (0 = don't change)
            if refresh_rate > 0:
                display.set_refresh_rate(refresh_rate)

            if success:
                self.config.set_active_profile(profile_name)
                if self.on_switch:
                    try:
                        self.on_switch(profile_name)
                    except Exception:
                        pass

            return success

    def get_active(self):
        """Return the name of the currently active profile."""
        return self.config.get_active_profile()

    def get_profile_names(self):
        """Return list of profile names."""
        return list(self.config.get_all_profiles().keys())

    def apply_preview(self, brightness, colour_temp):
        """Apply display settings without saving — for previewing in the UI."""
        display.apply_profile(brightness, colour_temp, transition_ms=0)

    def is_locked(self):
        """Check if profile lock is active."""
        return self.config.get("profile_lock", False)

    def toggle_lock(self):
        """Toggle profile lock. Returns new lock state."""
        locked = not self.config.get("profile_lock", False)
        self.config.set("profile_lock", locked)
        if self.on_lock_change:
            try:
                self.on_lock_change(locked)
            except Exception:
                pass
        return locked
