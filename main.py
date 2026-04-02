"""
Display Manager — Main Entry Point
Orchestrates all threads: tray, hotkeys, scheduler, watchdog, UI.
"""

import atexit
import sys
import threading
from pathlib import Path

# Ensure project directory is on path (for PyInstaller and direct running)
sys.path.insert(0, str(Path(__file__).parent))

import display
from config import Config
from profiles import ProfileManager
from tray import TrayApp
from hotkeys import HotkeyManager
from scheduler import ScheduleManager
from ui.settings_window import SettingsWindow
import autostart


def _run_watchdog(pm, stop_event):
    """Watchdog thread: re-applies profile if gamma ramp is reset (e.g., monitor wake)."""
    while not stop_event.is_set():
        stop_event.wait(10)  # check every 10 seconds
        if stop_event.is_set():
            break
        if not display.check_gamma_ramp_intact():
            active = pm.get_active()
            profile = pm.config.get_profile(active)
            if profile:
                display.set_colour_temperature(profile.get("colour_temp", 6500))
                display.set_brightness(profile.get("brightness", 70))


def main():
    # 1. Load config
    config = Config()

    # 2. Create profile manager
    pm = ProfileManager(config)

    # 3. Create settings window (root not yet shown)
    settings = SettingsWindow(config, pm)
    root = settings.init_root()

    # 4. Watchdog stop event
    watchdog_stop = threading.Event()

    # 5. Quit handler
    def quit_app():
        watchdog_stop.set()
        hk.stop()
        sm.stop()
        tray.stop()
        display.reset_colour_temperature()
        root.after(0, root.quit)

    # 6. Create and start tray
    tray = TrayApp(pm, on_settings=settings.show, on_quit=quit_app)
    pm.on_switch = tray.update_tooltip
    pm.on_lock_change = lambda locked: tray._update_icon()
    tray.start()

    # 7. Hotkeys
    hk = HotkeyManager(pm, config)
    hk.start()
    settings.hk = hk

    # 8. Scheduler
    sm = ScheduleManager(pm, config)
    sm.start()
    settings.sm = sm

    # 9. Watchdog thread (monitor wake recovery)
    watchdog = threading.Thread(target=_run_watchdog, args=(pm, watchdog_stop), daemon=True)
    watchdog.start()

    # 10. Sync auto-start registry with config
    autostart.sync_autostart(config)

    # 11. Apply last-used profile on startup
    config.set("profile_lock", False)  # always start unlocked
    active = config.get_active_profile()
    pm.switch(active, force=True)

    # 12. Safety net: reset gamma on any exit
    atexit.register(display.reset_colour_temperature)

    # 13. First-run check
    if not config.get("first_run_complete", False):
        root.after(500, lambda: _first_run_dialog(root, config))

    # 14. Main loop (blocks until quit)
    root.mainloop()

    # Cleanup after mainloop exits
    watchdog_stop.set()
    hk.stop()
    sm.stop()
    display.reset_colour_temperature()


def _first_run_dialog(root, config):
    """Show a first-run welcome dialog with system checks."""
    import subprocess
    import customtkinter as ctk

    dialog = ctk.CTkToplevel(root)
    dialog.title("Display Manager — Welcome")
    dialog.geometry("460x400")
    dialog.resizable(False, False)
    dialog.attributes("-topmost", True)

    ctk.CTkLabel(dialog, text="Welcome to Display Manager",
                  font=ctk.CTkFont(size=18, weight="bold")).pack(padx=20, pady=(15, 5))

    ctk.CTkLabel(dialog, text="Running system checks...",
                  text_color="gray").pack(padx=20, pady=(0, 10))

    results_frame = ctk.CTkFrame(dialog)
    results_frame.pack(padx=15, pady=5, fill="both", expand=True)

    checks = []

    # DDC/CI check
    ddc_ok, ddc_msg = display.check_ddc_available()
    if ddc_ok:
        checks.append(("DDC/CI Monitor", ddc_msg, "green"))
    else:
        checks.append(("DDC/CI Monitor", ddc_msg, "orange"))

    # Refresh rates
    rates = display.get_available_refresh_rates()
    if rates:
        checks.append(("Refresh Rates", f"Available: {', '.join(str(r) for r in rates)} Hz", "green"))
    else:
        checks.append(("Refresh Rates", "Could not enumerate", "gray"))

    # f.lux check
    flux_running = False
    try:
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq flux.exe"],
            capture_output=True, text=True, timeout=5
        )
        if "flux.exe" in result.stdout.lower():
            flux_running = True
    except Exception:
        pass

    if flux_running:
        checks.append(("f.lux", "Running — please close f.lux to avoid conflicts.\n"
                        "Display Manager replaces f.lux for colour temperature.", "orange"))
    else:
        checks.append(("f.lux", "Not running (good)", "green"))

    # Location check
    sun_config = config.get("sun_schedule", {})
    lat = sun_config.get("latitude", 0)
    lon = sun_config.get("longitude", 0)
    if lat == 0 and lon == 0:
        checks.append(("Location", "Not set — go to Settings > Schedule > Detect\n"
                        "to enable sunrise/sunset auto-switching", "orange"))
    else:
        checks.append(("Location", f"Set to {lat}, {lon}", "green"))

    for name, msg, colour in checks:
        row = ctk.CTkFrame(results_frame, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=3)
        indicator = "OK" if colour == "green" else "!"
        ctk.CTkLabel(row, text=indicator, width=25,
                      text_color=colour, font=ctk.CTkFont(weight="bold")).pack(side="left")
        ctk.CTkLabel(row, text=f"{name}: {msg}", anchor="w",
                      wraplength=380, justify="left").pack(side="left", padx=5)

    ctk.CTkLabel(dialog, text="Tip: Right-click the tray icon to switch profiles\n"
                  "or press Ctrl+Alt+1/2/3 for quick switching.",
                  text_color="gray", justify="center").pack(padx=20, pady=(5, 5))

    def close():
        config.set("first_run_complete", True)
        dialog.destroy()

    ctk.CTkButton(dialog, text="Got it!", width=120, command=close).pack(pady=(5, 15))


if __name__ == "__main__":
    main()
