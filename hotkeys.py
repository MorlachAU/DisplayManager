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

        # Panic button — instant Work mode
        try:
            keyboard.add_hotkey("ctrl+alt+p", self._on_panic, suppress=False)
            self._registered.append("ctrl+alt+p")
        except Exception:
            pass

        # Disco mode — easter egg
        try:
            keyboard.add_hotkey("ctrl+alt+shift+d", self._on_disco, suppress=False)
            self._registered.append("ctrl+alt+shift+d")
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

    def _on_panic(self):
        self.pm.switch("Work", force=True)

    def _on_disco(self):
        import display
        if not display.is_disco_running():
            active = self.pm.get_active()
            display.start_disco(duration=5.0)
            import threading
            def restore():
                import time
                time.sleep(5.5)
                profile = self.pm.config.get_profile(active)
                if profile:
                    display.set_colour_temperature(profile.get("colour_temp", 6500))
            threading.Thread(target=restore, daemon=True).start()
