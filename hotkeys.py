"""
Display Manager — Global Hotkeys
Registers configurable hotkeys for profile switching, quick dim, and lock.
"""

import keyboard


class HotkeyManager:
    def __init__(self, profile_manager, config, on_dim_toggle=None):
        self.pm = profile_manager
        self.config = config
        self.on_dim_toggle = on_dim_toggle  # callback(is_dimmed) for UI updates
        self._registered = []

    def start(self):
        """Register all hotkeys from config."""
        import display

        # Profile hotkeys
        profiles = self.config.get_all_profiles()
        for name, profile in profiles.items():
            hotkey = profile.get("hotkey", "")
            if hotkey:
                try:
                    cb = self._make_switch_handler(name)
                    keyboard.add_hotkey(hotkey, cb, suppress=False)
                    self._registered.append(hotkey)
                except Exception:
                    pass

        # Quick dim hotkey
        dim_hotkey = self.config.get("quick_dim_hotkey", "ctrl+alt+d")
        if dim_hotkey:
            try:
                keyboard.add_hotkey(dim_hotkey, self._on_dim, suppress=False)
                self._registered.append(dim_hotkey)
            except Exception:
                pass

        # Lock toggle hotkey
        try:
            keyboard.add_hotkey("ctrl+alt+l", self._on_lock, suppress=False)
            self._registered.append("ctrl+alt+l")
        except Exception:
            pass

    def stop(self):
        """Unregister all hotkeys."""
        for hotkey in self._registered:
            try:
                keyboard.remove_hotkey(hotkey)
            except Exception:
                pass
        self._registered.clear()

    def reload(self):
        """Re-register hotkeys after config change."""
        self.stop()
        self.start()

    def _make_switch_handler(self, profile_name):
        def handler():
            # Manual hotkey always forces (bypasses lock)
            self.pm.switch(profile_name, force=True)
        return handler

    def _on_dim(self):
        import display
        is_dimmed = display.toggle_quick_dim()
        if self.on_dim_toggle:
            try:
                self.on_dim_toggle(is_dimmed)
            except Exception:
                pass

    def _on_lock(self):
        self.pm.toggle_lock()
