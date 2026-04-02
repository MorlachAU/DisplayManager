"""
Display Manager — System Tray
pystray-based tray icon with profile switching menu and per-profile colours.
"""

import threading
from pathlib import Path
from PIL import Image, ImageDraw
import pystray

# Profile icon colours
PROFILE_COLOURS = {
    "Work": (80, 140, 255),    # Blue
    "Code": (255, 180, 50),    # Amber
    "Game": (50, 200, 80),     # Green
}
DEFAULT_COLOUR = (100, 180, 255)
LOCK_COLOUR = (200, 50, 50)  # Red tint when locked


def _generate_icon(colour, size=64, locked=False):
    """Generate a tray icon with the given colour."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Background circle
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=colour + (255,))

    # Monitor outline in center
    mx = size * 0.28
    my = size * 0.26
    mw = size * 0.44
    mh = size * 0.32
    draw.rounded_rectangle(
        [mx, my, mx + mw, my + mh],
        radius=max(1, size // 20),
        outline=(255, 255, 255, 200),
        width=max(1, size // 20)
    )

    # Screen fill
    pad = max(1, size // 25)
    draw.rectangle(
        [mx + pad, my + pad, mx + mw - pad, my + mh - pad],
        fill=(255, 255, 255, 80)
    )

    # Stand
    cx = size // 2
    stand_top = my + mh
    draw.rectangle(
        [cx - size * 0.04, stand_top, cx + size * 0.04, stand_top + size * 0.06],
        fill=(255, 255, 255, 200)
    )

    # Lock indicator (small dot in bottom-right)
    if locked:
        lr = size * 0.12
        lx = size - margin - lr
        ly = size - margin - lr
        draw.ellipse([lx, ly, lx + lr * 2, ly + lr * 2],
                     fill=LOCK_COLOUR + (255,))

    return img


class TrayApp:
    def __init__(self, profile_manager, on_settings=None, on_quit=None):
        self.pm = profile_manager
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon = None
        self._thread = None

        # Pre-generate icons for each profile
        self._icons = {}
        self._icons_locked = {}
        for name, colour in PROFILE_COLOURS.items():
            self._icons[name] = _generate_icon(colour)
            self._icons_locked[name] = _generate_icon(colour, locked=True)
        self._default_icon = _generate_icon(DEFAULT_COLOUR)

    def _get_icon_for_profile(self, name):
        """Get the appropriate icon for a profile, considering lock state."""
        locked = self.pm.is_locked()
        if locked:
            return self._icons_locked.get(name, self._default_icon)
        return self._icons.get(name, self._default_icon)

    def _build_menu(self):
        """Build the tray context menu."""
        profile_items = []
        for name in self.pm.get_profile_names():
            profile_items.append(
                pystray.MenuItem(
                    name,
                    self._make_switch_handler(name),
                    checked=lambda item, n=name: self.pm.get_active() == n,
                    radio=True,
                )
            )

        lock_text = "Unlock Profile" if self.pm.is_locked() else "Lock Profile"

        return pystray.Menu(
            *profile_items,
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(lock_text, self._on_lock_click),
            pystray.MenuItem("Settings", self._on_settings_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_click),
        )

    def _make_switch_handler(self, profile_name):
        """Create a menu handler for switching to a specific profile."""
        def handler(icon, item):
            # Manual switch always forces (bypasses lock)
            self.pm.switch(profile_name, force=True)
        return handler

    def _on_lock_click(self, icon, item):
        self.pm.toggle_lock()
        self._update_icon()

    def _on_settings_click(self, icon, item):
        if self._on_settings:
            self._on_settings()

    def _on_quit_click(self, icon, item):
        if self._on_quit:
            self._on_quit()

    def start(self):
        """Start the tray icon in a daemon thread."""
        active = self.pm.get_active()
        self._icon = pystray.Icon(
            "DisplayManager",
            self._get_icon_for_profile(active),
            title=self._build_title(active),
            menu=self._build_menu(),
        )
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the tray icon."""
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass

    def _build_title(self, profile_name):
        locked = " [LOCKED]" if self.pm.is_locked() else ""
        return f"Display Manager - {profile_name}{locked}"

    def update_tooltip(self, profile_name):
        """Update tray tooltip and icon when profile changes."""
        if self._icon:
            self._icon.title = self._build_title(profile_name)
            self._icon.icon = self._get_icon_for_profile(profile_name)

    def _update_icon(self):
        """Refresh the icon (e.g., after lock state change)."""
        if self._icon:
            active = self.pm.get_active()
            self._icon.title = self._build_title(active)
            self._icon.icon = self._get_icon_for_profile(active)
