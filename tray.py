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
    "Cinema": (180, 60, 180),  # Purple
}
DEFAULT_COLOUR = (100, 180, 255)
LOCK_COLOUR = (220, 50, 50)

# Cache the MouseWheel logo
_logo_cache = {}


def _load_logo(size):
    """Load and cache the MouseWheel logo at a given size."""
    if size in _logo_cache:
        return _logo_cache[size]
    logo_path = Path(__file__).parent / "assets" / "mousewheel_logo.png"
    if logo_path.exists():
        logo = Image.open(str(logo_path)).convert("RGBA")
        # Fit logo into the icon area (with padding for the ring)
        logo_size = int(size * 0.6)
        logo = logo.resize((logo_size, logo_size), Image.LANCZOS)
        _logo_cache[size] = logo
        return logo
    return None


def _generate_icon(colour, size=64, locked=False):
    """Generate a tray icon with coloured ring and MouseWheel logo."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Coloured ring background
    margin = size // 16
    ring_width = max(3, size // 10)
    draw.ellipse([margin, margin, size - margin, size - margin],
                 fill=colour + (255,))

    # Dark inner circle (logo background)
    inner_margin = margin + ring_width
    draw.ellipse([inner_margin, inner_margin,
                  size - inner_margin, size - inner_margin],
                 fill=(20, 25, 35, 255))

    # Paste MouseWheel logo in center
    logo = _load_logo(size)
    if logo:
        lx = (size - logo.width) // 2
        ly = (size - logo.height) // 2
        img.paste(logo, (lx, ly), logo)

    # Lock indicator (small red dot in bottom-right)
    if locked:
        lr = size * 0.14
        lx = size - margin - lr * 1.5
        ly = size - margin - lr * 1.5
        draw.ellipse([lx, ly, lx + lr * 2, ly + lr * 2],
                     fill=LOCK_COLOUR + (255,),
                     outline=(255, 255, 255, 200), width=max(1, size // 32))

    return img


class TrayApp:
    def __init__(self, profile_manager, config, on_settings=None, on_quit=None):
        self.pm = profile_manager
        self.config = config
        self._on_settings = on_settings
        self._on_quit = on_quit
        self._icon = None
        self._thread = None

        # Generate icons for all profiles
        self._icons = {}
        self._icons_locked = {}
        self._default_icon = _generate_icon(DEFAULT_COLOUR)
        self._rebuild_icons()

    def _rebuild_icons(self):
        """Regenerate icons for all current profiles."""
        for name in self.pm.get_profile_names():
            if name not in self._icons:
                colour = PROFILE_COLOURS.get(name, DEFAULT_COLOUR)
                self._icons[name] = _generate_icon(colour)
                self._icons_locked[name] = _generate_icon(colour, locked=True)

    def refresh_profiles(self):
        """Called when profiles are added/removed. Rebuilds icons and updates menu."""
        self._rebuild_icons()
        self._update_icon()

    def _get_icon_for_profile(self, name):
        """Get the appropriate icon for a profile, considering lock state."""
        locked = self.pm.is_locked()
        if locked:
            return self._icons_locked.get(name, self._default_icon)
        return self._icons.get(name, self._default_icon)

    def _build_menu(self):
        """Build the tray context menu (static, used at startup)."""
        return pystray.Menu(lambda: self._build_menu_items())

    def _build_menu_items(self):
        """Build menu items dynamically — called each time the menu opens."""
        items = []
        for name in self.pm.get_profile_names():
            items.append(
                pystray.MenuItem(
                    name,
                    self._make_switch_handler(name),
                    checked=lambda item, n=name: self.pm.get_active() == n,
                    radio=True,
                )
            )

        items.append(pystray.MenuItem(
            "Ambient",
            self._on_ambient_click,
            checked=lambda item: self.config.get("ambient_mode", False),
        ))

        lock_text = "Unlock Profile" if self.pm.is_locked() else "Lock Profile"

        items.extend([
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("PANIC! (Work mode)", self._on_panic_click),
            pystray.MenuItem(lock_text, self._on_lock_click),
            pystray.MenuItem("Disco Mode", self._on_disco_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Settings", self._on_settings_click),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", self._on_quit_click),
        ])
        return items

    def _make_switch_handler(self, profile_name):
        """Create a menu handler for switching to a specific profile."""
        def handler(icon, item):
            # Manual switch always forces (bypasses lock)
            self.pm.switch(profile_name, force=True)
        return handler

    def _on_ambient_click(self, icon, item):
        """Toggle ambient mode on/off. Enabling unlocks the profile so it can adjust."""
        current = self.config.get("ambient_mode", False)
        self.config.set("ambient_mode", not current)
        if not current:
            # Turning ambient ON — unlock so it can adjust freely
            self.config.set("profile_lock", False)
            self._update_icon()

    def _on_panic_click(self, icon, item):
        """PANIC! Instantly switch to Work and close settings."""
        self.pm.switch("Work", force=True)

    def _on_disco_click(self, icon, item):
        """Easter egg: disco mode!"""
        import display
        if not display.is_disco_running():
            # Remember current profile to restore after
            active = self.pm.get_active()
            display.start_disco(duration=5.0)
            # Restore profile after disco ends
            import threading
            def restore():
                import time
                time.sleep(5.5)
                profile = self.pm.config.get_profile(active)
                if profile:
                    display.set_colour_temperature(profile.get("colour_temp", 6500))
            threading.Thread(target=restore, daemon=True).start()

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
            menu=pystray.Menu(lambda: self._build_menu_items()),
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
            # Show notification toast
            if self.config.get("notifications_enabled", True):
                try:
                    self._icon.notify(
                        f"Switched to {profile_name}",
                        "Display Manager"
                    )
                except Exception:
                    pass

    def _update_icon(self):
        """Refresh the icon (e.g., after lock state change)."""
        if self._icon:
            active = self.pm.get_active()
            self._icon.title = self._build_title(active)
            self._icon.icon = self._get_icon_for_profile(active)
