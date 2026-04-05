"""
Display Manager — Settings Window
customtkinter tabbed settings UI.
"""

import threading
import customtkinter as ctk
import display
import autostart


class SettingsWindow:
    def __init__(self, config, profile_manager):
        self.config = config
        self.pm = profile_manager
        self.hk = None   # HotkeyManager — wired after construction
        self.sm = None   # ScheduleManager — wired after construction
        self.stats = None  # StatsTracker — wired after construction
        self._root = None
        self._window = None

    def init_root(self):
        """Create the hidden root window. Must be called on main thread."""
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self._root = ctk.CTk()
        self._root.withdraw()
        self._root.title("Display Manager")
        return self._root

    def show(self):
        """Show the settings window. Safe to call from any thread."""
        if self._root:
            self._root.after(0, self._create_or_focus)

    def _load_header_logo(self, parent):
        """Load MouseWheel Digital logo into the settings header."""
        from pathlib import Path
        from PIL import Image, ImageTk
        logo_path = Path(__file__).parent.parent / "assets" / "mousewheel_logo.png"
        try:
            if logo_path.exists():
                logo = Image.open(str(logo_path)).convert("RGBA")
                logo = logo.resize((32, 32), Image.LANCZOS)
                self._header_logo_img = ImageTk.PhotoImage(logo)
                ctk.CTkLabel(parent, image=self._header_logo_img, text="").pack(side="left", padx=(5, 8))
            ctk.CTkLabel(parent, text="Display Manager",
                          font=ctk.CTkFont(size=16, weight="bold")).pack(side="left")
            ctk.CTkLabel(parent, text="by MouseWheel Digital",
                          text_color="gray", font=ctk.CTkFont(size=11)).pack(side="left", padx=(8, 0))
        except Exception:
            ctk.CTkLabel(parent, text="Display Manager",
                          font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=5)

    def _create_or_focus(self):
        """Create the settings window or focus it if already open."""
        if self._window and self._window.winfo_exists():
            self._window.focus_force()
            self._window.lift()
            return
        self._create_window()

    def _create_window(self):
        """Build the settings window."""
        self._window = ctk.CTkToplevel(self._root)
        self._window.title("Display Manager — Settings")
        self._window.geometry("580x650")
        self._window.resizable(False, False)
        self._window.attributes("-topmost", True)
        self._window.after(200, lambda: self._window.attributes("-topmost", False))

        # Branding header
        header = ctk.CTkFrame(self._window, height=40, fg_color="transparent")
        header.pack(padx=10, pady=(8, 0), fill="x")
        self._load_header_logo(header)

        # Tabs
        tabs = ctk.CTkTabview(self._window, width=490, height=430)
        tabs.pack(padx=10, pady=(0, 10), fill="both", expand=True)

        self._build_profiles_tab(tabs.add("Profiles"))
        self._build_schedule_tab(tabs.add("Schedule"))
        self._build_apps_tab(tabs.add("Apps"))
        self._build_general_tab(tabs.add("General"))
        self._build_stats_tab(tabs.add("Stats"))
        self._build_about_tab(tabs.add("About"))

    # ── Profiles Tab ───────────────────────────────────────

    def _build_profiles_tab(self, tab):
        self._profile_widgets = {}
        self._profiles_tab = tab

        # Top row: profile selector + add/delete buttons
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(padx=10, pady=(10, 0), fill="x")

        self._selector_frame = ctk.CTkFrame(top, fg_color="transparent")
        self._selector_frame.pack(side="left", fill="x", expand=True)

        names = self.pm.get_profile_names()
        self._selected_profile = ctk.StringVar(value=names[0] if names else "Work")

        self._profile_selector = ctk.CTkSegmentedButton(
            self._selector_frame, values=names, variable=self._selected_profile,
            command=self._on_profile_selected
        )
        self._profile_selector.pack(fill="x")

        btn_frame = ctk.CTkFrame(top, fg_color="transparent")
        btn_frame.pack(side="right", padx=(5, 0))
        ctk.CTkButton(btn_frame, text="+", width=30, command=self._add_profile).pack(side="left", padx=1)
        ctk.CTkButton(btn_frame, text="-", width=30, fg_color="firebrick",
                       command=self._delete_profile).pack(side="left", padx=1)

        # Brightness
        ctk.CTkLabel(tab, text="Brightness", anchor="w").pack(padx=15, pady=(10, 0), anchor="w")
        bf = ctk.CTkFrame(tab, fg_color="transparent")
        bf.pack(padx=10, fill="x")

        self._brightness_var = ctk.IntVar(value=70)
        self._brightness_label = ctk.CTkLabel(bf, text="70%", width=45)
        self._brightness_label.pack(side="right", padx=5)
        self._brightness_slider = ctk.CTkSlider(
            bf, from_=0, to=100, variable=self._brightness_var,
            command=self._on_brightness_change
        )
        self._brightness_slider.pack(side="left", fill="x", expand=True, padx=5)

        # Colour temperature
        ctk.CTkLabel(tab, text="Colour Temperature", anchor="w").pack(padx=15, pady=(10, 0), anchor="w")
        cf = ctk.CTkFrame(tab, fg_color="transparent")
        cf.pack(padx=10, fill="x")

        self._temp_var = ctk.IntVar(value=6500)
        self._temp_label = ctk.CTkLabel(cf, text="6500K", width=55)
        self._temp_label.pack(side="right", padx=5)
        self._temp_slider = ctk.CTkSlider(
            cf, from_=1200, to=6500, variable=self._temp_var,
            command=self._on_temp_change
        )
        self._temp_slider.pack(side="left", fill="x", expand=True, padx=5)

        # Refresh rate
        ctk.CTkLabel(tab, text="Refresh Rate", anchor="w").pack(padx=15, pady=(10, 0), anchor="w")
        rf = ctk.CTkFrame(tab, fg_color="transparent")
        rf.pack(padx=10, fill="x")

        available_rates = display.get_available_refresh_rates()
        rate_options = ["No change"] + [f"{r} Hz" for r in available_rates]
        self._refresh_var = ctk.StringVar(value="No change")
        ctk.CTkOptionMenu(rf, values=rate_options, variable=self._refresh_var,
                           width=120).pack(side="left", padx=5)

        # Hotkey
        ctk.CTkLabel(tab, text="Hotkey", anchor="w").pack(padx=15, pady=(10, 0), anchor="w")
        hf = ctk.CTkFrame(tab, fg_color="transparent")
        hf.pack(padx=10, fill="x")

        self._hotkey_var = ctk.StringVar(value="")
        self._hotkey_entry = ctk.CTkEntry(hf, textvariable=self._hotkey_var, width=200)
        self._hotkey_entry.pack(side="left", padx=5)

        self._record_btn = ctk.CTkButton(hf, text="Record", width=80,
                                          command=self._record_hotkey)
        self._record_btn.pack(side="left", padx=5)

        # Buttons
        btnf = ctk.CTkFrame(tab, fg_color="transparent")
        btnf.pack(padx=10, pady=15, fill="x")

        ctk.CTkButton(btnf, text="Apply Now", width=100,
                       command=self._apply_preview).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Save", width=100,
                       command=self._save_profile).pack(side="left", padx=5)

        btnf2 = ctk.CTkFrame(tab, fg_color="transparent")
        btnf2.pack(padx=10, fill="x")
        ctk.CTkButton(btnf2, text="Revert to Default", width=130, fg_color="gray30",
                       command=self._revert_profile).pack(side="left", padx=5)
        ctk.CTkButton(btnf2, text="Restore All Defaults", width=140, fg_color="gray30",
                       command=self._restore_all_defaults).pack(side="left", padx=5)

        # Status
        self._profile_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self._profile_status.pack(padx=15, anchor="w")

        # Load first profile
        self._on_profile_selected(self._selected_profile.get())

    def _on_profile_selected(self, name):
        """Load profile values into the editor widgets."""
        profile = self.config.get_profile(name)
        if profile:
            self._brightness_var.set(profile.get("brightness", 70))
            self._brightness_label.configure(text=f"{profile.get('brightness', 70)}%")
            self._temp_var.set(profile.get("colour_temp", 6500))
            self._temp_label.configure(text=f"{profile.get('colour_temp', 6500)}K")
            self._hotkey_var.set(profile.get("hotkey", ""))
            rr = profile.get("refresh_rate", 0)
            self._refresh_var.set(f"{rr} Hz" if rr > 0 else "No change")

    def _on_brightness_change(self, value):
        self._brightness_label.configure(text=f"{int(value)}%")

    def _on_temp_change(self, value):
        self._temp_label.configure(text=f"{int(value)}K")

    def _revert_profile(self):
        """Revert the selected profile to factory defaults."""
        from config import DEFAULTS
        name = self._selected_profile.get()
        default_profile = DEFAULTS["profiles"].get(name)
        if default_profile:
            self.config.set_profile(name, dict(default_profile))
            self._on_profile_selected(name)
            self._profile_status.configure(text=f"Reverted {name} to defaults")

    def _add_profile(self):
        """Add a new custom profile via dialog."""
        dialog = ctk.CTkInputDialog(text="Enter profile name:", title="New Profile")
        name = dialog.get_input()
        if not name or not name.strip():
            return
        name = name.strip()
        # Check for duplicate
        if self.config.get_profile(name):
            self._profile_status.configure(text=f"Profile '{name}' already exists")
            return
        # Create with sensible defaults
        new_profile = {"brightness": 70, "colour_temp": 6500, "hotkey": "", "refresh_rate": 0}
        self.config.set_profile(name, new_profile)
        self._rebuild_selector(name)
        if self.hk:
            self.hk.reload()
        self._profile_status.configure(text=f"Created profile '{name}'")

    def _delete_profile(self):
        """Delete the selected profile."""
        name = self._selected_profile.get()
        profiles = self.config.get_all_profiles()
        # Must keep at least one profile
        if len(profiles) <= 1:
            self._profile_status.configure(text="Cannot delete the last profile")
            return
        # Remove from config
        if name in profiles:
            del profiles[name]
            self.config.set("profiles", profiles)
        # If active profile was deleted, switch to first remaining
        if self.pm.get_active() == name:
            first = list(profiles.keys())[0]
            self.pm.switch(first, force=True)
        # Rebuild selector
        remaining = list(profiles.keys())
        self._rebuild_selector(remaining[0] if remaining else "Work")
        if self.hk:
            self.hk.reload()
        self._profile_status.configure(text=f"Deleted profile '{name}'")

    def _restore_all_defaults(self):
        """Restore all built-in profiles to factory defaults (keeps custom profiles)."""
        from config import DEFAULTS
        profiles = self.config.get_all_profiles()
        for name, default_profile in DEFAULTS["profiles"].items():
            profiles[name] = dict(default_profile)
        self.config.set("profiles", profiles)
        self._rebuild_selector(self._selected_profile.get())
        if self.hk:
            self.hk.reload()
        self._profile_status.configure(text="Restored all default profiles")

    def _rebuild_selector(self, select_name=None):
        """Rebuild the profile selector with current profiles."""
        names = self.pm.get_profile_names()
        self._profile_selector.configure(values=names)
        if select_name and select_name in names:
            self._selected_profile.set(select_name)
        elif names:
            self._selected_profile.set(names[0])
        self._on_profile_selected(self._selected_profile.get())
        # Notify tray to rebuild its icons/menu
        if hasattr(self, '_on_profiles_changed') and self._on_profiles_changed:
            self._on_profiles_changed()

    def _apply_preview(self):
        """Preview current slider values without saving."""
        b = int(self._brightness_var.get())
        k = int(self._temp_var.get())
        threading.Thread(target=self.pm.apply_preview, args=(b, k), daemon=True).start()
        self._profile_status.configure(text=f"Preview: {b}% brightness, {k}K")

    def _save_profile(self):
        """Save current values to the selected profile."""
        name = self._selected_profile.get()
        rr_str = self._refresh_var.get()
        rr = int(rr_str.replace(" Hz", "")) if rr_str != "No change" else 0
        profile = {
            "brightness": int(self._brightness_var.get()),
            "colour_temp": int(self._temp_var.get()),
            "hotkey": self._hotkey_var.get().strip(),
            "refresh_rate": rr,
        }
        self.config.set_profile(name, profile)

        # Reload hotkeys if they changed
        if self.hk:
            self.hk.reload()

        # If this is the active profile, apply immediately
        if name == self.pm.get_active():
            threading.Thread(target=self.pm.switch, args=(name,), daemon=True).start()

        self._profile_status.configure(text=f"Saved {name} profile")

    def _record_hotkey(self):
        """Record a hotkey combo from the keyboard."""
        self._record_btn.configure(text="Press keys...", state="disabled")

        def do_record():
            import keyboard
            combo = keyboard.read_hotkey(suppress=False)
            if self._root:
                self._root.after(0, lambda: self._finish_record(combo))

        threading.Thread(target=do_record, daemon=True).start()

    def _finish_record(self, combo):
        self._hotkey_var.set(combo)
        self._record_btn.configure(text="Record", state="normal")

    # ── Schedule Tab ───────────────────────────────────────

    def _build_schedule_tab(self, tab):
        # ── Sunrise/Sunset section ──
        sun_config = self.config.get("sun_schedule", {})

        ctk.CTkLabel(tab, text="Sunrise / Sunset", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(10, 2), anchor="w")

        self._sun_enabled_var = ctk.BooleanVar(value=sun_config.get("enabled", False))
        ctk.CTkSwitch(
            tab, text="Auto-switch at sunrise and sunset",
            variable=self._sun_enabled_var,
            command=self._on_sun_toggle
        ).pack(padx=15, pady=(2, 5), anchor="w")

        sun_frame = ctk.CTkFrame(tab, fg_color="transparent")
        sun_frame.pack(padx=10, fill="x", pady=(0, 5))

        names = self.pm.get_profile_names()

        ctk.CTkLabel(sun_frame, text="Sunrise:").pack(side="left", padx=(5, 2))
        self._sunrise_profile_var = ctk.StringVar(value=sun_config.get("sunrise_profile", "Work"))
        ctk.CTkOptionMenu(sun_frame, values=names, variable=self._sunrise_profile_var,
                           width=100).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(sun_frame, text="Sunset:").pack(side="left", padx=(5, 2))
        self._sunset_profile_var = ctk.StringVar(value=sun_config.get("sunset_profile", "Code"))
        ctk.CTkOptionMenu(sun_frame, values=names, variable=self._sunset_profile_var,
                           width=100).pack(side="left", padx=(0, 10))

        # Location
        loc_frame = ctk.CTkFrame(tab, fg_color="transparent")
        loc_frame.pack(padx=10, fill="x", pady=(0, 5))

        ctk.CTkLabel(loc_frame, text="Lat:").pack(side="left", padx=(5, 2))
        self._lat_var = ctk.StringVar(value=str(sun_config.get("latitude", 0.0)))
        ctk.CTkEntry(loc_frame, textvariable=self._lat_var, width=80).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(loc_frame, text="Lon:").pack(side="left", padx=(5, 2))
        self._lon_var = ctk.StringVar(value=str(sun_config.get("longitude", 0.0)))
        ctk.CTkEntry(loc_frame, textvariable=self._lon_var, width=80).pack(side="left", padx=(0, 10))

        ctk.CTkButton(loc_frame, text="Detect", width=60,
                       command=self._detect_location).pack(side="left", padx=5)

        # Show today's sun times
        self._sun_times_label = ctk.CTkLabel(loc_frame, text="", text_color="gray")
        self._sun_times_label.pack(side="left", padx=5)
        self._refresh_sun_times()

        ctk.CTkButton(tab, text="Save Sun Schedule", width=140,
                       command=self._save_sun_schedule).pack(padx=10, pady=(0, 5), anchor="w")

        # ── Fixed time rules section ──
        ctk.CTkLabel(tab, text="Fixed Time Rules", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(5, 2), anchor="w")

        self._schedule_enabled_var = ctk.BooleanVar(
            value=self.config.get("schedule_enabled", False)
        )
        ctk.CTkSwitch(
            tab, text="Enable fixed time rules",
            variable=self._schedule_enabled_var,
            command=self._on_schedule_toggle
        ).pack(padx=15, pady=(2, 5), anchor="w")

        # Rules frame
        self._rules_frame = ctk.CTkScrollableFrame(tab, height=120)
        self._rules_frame.pack(padx=10, pady=2, fill="both", expand=True)

        self._rule_widgets = []
        rules = self.config.get_schedule_rules()
        for rule in rules:
            self._add_rule_row(rule.get("time", ""), rule.get("profile", "Work"))

        btnf = ctk.CTkFrame(tab, fg_color="transparent")
        btnf.pack(padx=10, pady=2, fill="x")
        ctk.CTkButton(btnf, text="+ Add Rule", width=100,
                       command=lambda: self._add_rule_row("12:00", "Work")).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Save Rules", width=100,
                       command=self._save_schedule).pack(side="left", padx=5)

        self._schedule_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self._schedule_status.pack(padx=15, anchor="w")

    def _add_rule_row(self, time_str, profile_name):
        """Add a schedule rule row to the rules frame."""
        row = ctk.CTkFrame(self._rules_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)

        time_var = ctk.StringVar(value=time_str)
        ctk.CTkEntry(row, textvariable=time_var, width=80,
                      placeholder_text="HH:MM").pack(side="left", padx=5)

        profile_var = ctk.StringVar(value=profile_name)
        names = self.pm.get_profile_names()
        ctk.CTkOptionMenu(row, values=names, variable=profile_var,
                           width=120).pack(side="left", padx=5)

        def remove():
            row.destroy()
            self._rule_widgets = [(t, p, r) for t, p, r in self._rule_widgets if r != row]

        ctk.CTkButton(row, text="X", width=30, fg_color="firebrick",
                       command=remove).pack(side="left", padx=5)

        self._rule_widgets.append((time_var, profile_var, row))

    def _detect_location(self):
        """Detect location via IP geolocation."""
        self._schedule_status.configure(text="Detecting location...")

        def do_detect():
            import urllib.request
            import json
            try:
                req = urllib.request.urlopen("http://ip-api.com/json/?fields=lat,lon,city,country", timeout=5)
                data = json.loads(req.read().decode())
                lat = data.get("lat", 0)
                lon = data.get("lon", 0)
                city = data.get("city", "")
                country = data.get("country", "")
                if self._root:
                    self._root.after(0, lambda: self._apply_detected_location(lat, lon, city, country))
            except Exception:
                if self._root:
                    self._root.after(0, lambda: self._schedule_status.configure(
                        text="Location detection failed — enter manually"))

        threading.Thread(target=do_detect, daemon=True).start()

    def _apply_detected_location(self, lat, lon, city, country):
        self._lat_var.set(str(round(lat, 2)))
        self._lon_var.set(str(round(lon, 2)))
        label = f"{city}, {country}" if city else f"{lat}, {lon}"
        self._schedule_status.configure(text=f"Detected: {label}")

    def _on_sun_toggle(self):
        self._save_sun_schedule()

    def _save_sun_schedule(self):
        try:
            lat = float(self._lat_var.get())
            lon = float(self._lon_var.get())
        except ValueError:
            self._schedule_status.configure(text="Invalid lat/lon values")
            return
        sun_config = {
            "enabled": self._sun_enabled_var.get(),
            "latitude": lat,
            "longitude": lon,
            "sunrise_profile": self._sunrise_profile_var.get(),
            "sunset_profile": self._sunset_profile_var.get(),
        }
        self.config.set("sun_schedule", sun_config)
        if self.sm:
            self.sm.reload()
        self._refresh_sun_times()
        self._schedule_status.configure(text="Sun schedule saved")

    def _refresh_sun_times(self):
        if self.sm:
            sunrise, sunset = self.sm.get_sun_times()
            if sunrise and sunset:
                self._sun_times_label.configure(text=f"Today: {sunrise} / {sunset}")

    def _on_schedule_toggle(self):
        self.config.set("schedule_enabled", self._schedule_enabled_var.get())
        if self.sm:
            self.sm.reload()

    def _save_schedule(self):
        rules = []
        for time_var, profile_var, row in self._rule_widgets:
            if row.winfo_exists():
                t = time_var.get().strip()
                p = profile_var.get()
                if t and p:
                    rules.append({"time": t, "profile": p})
        self.config.set_schedule_rules(rules)
        if self.sm:
            self.sm.reload()
        self._schedule_status.configure(text=f"Saved {len(rules)} rule(s)")

    # ── General Tab ────────────────────────────────────────

    # ── Apps Tab ────────────────────────────────────────────

    def _build_apps_tab(self, tab):
        # App-aware toggle
        self._app_aware_var = ctk.BooleanVar(value=self.config.get("app_aware_enabled", True))
        ctk.CTkSwitch(
            tab, text="Enable app-aware profile switching",
            variable=self._app_aware_var,
            command=lambda: self.config.set("app_aware_enabled", self._app_aware_var.get())
        ).pack(padx=15, pady=(10, 2), anchor="w")

        ctk.CTkLabel(tab, text="Automatically detects games and switches profiles.\n"
                      "Games are detected via Windows, Steam, Epic, fullscreen, and DirectX.",
                      text_color="gray", justify="left", font=ctk.CTkFont(size=11)).pack(padx=20, pady=(0, 5), anchor="w")

        # Game detection profile
        gf = ctk.CTkFrame(tab, fg_color="transparent")
        gf.pack(padx=10, fill="x", pady=(0, 3))
        ctk.CTkLabel(gf, text="When a game is detected, switch to:").pack(side="left", padx=5)
        self._game_profile_var = ctk.StringVar(value=self.config.get("game_detect_profile", "Game"))
        ctk.CTkOptionMenu(gf, values=self.pm.get_profile_names(),
                           variable=self._game_profile_var, width=120,
                           command=lambda v: self.config.set("game_detect_profile", v)).pack(side="left", padx=5)

        # Productivity detection profile
        self._productivity_enabled_var = ctk.BooleanVar(
            value=self.config.get("productivity_detect_enabled", False))
        ctk.CTkSwitch(
            tab, text="Detect productivity apps (Office, browsers, Teams, etc.)",
            variable=self._productivity_enabled_var,
            command=lambda: self.config.set("productivity_detect_enabled",
                                             self._productivity_enabled_var.get())
        ).pack(padx=15, pady=(3, 2), anchor="w")

        pf = ctk.CTkFrame(tab, fg_color="transparent")
        pf.pack(padx=10, fill="x", pady=(0, 5))
        ctk.CTkLabel(pf, text="When a productivity app is detected, switch to:").pack(side="left", padx=5)
        self._prod_profile_var = ctk.StringVar(value=self.config.get("productivity_detect_profile", "Work"))
        ctk.CTkOptionMenu(pf, values=self.pm.get_profile_names(),
                           variable=self._prod_profile_var, width=120,
                           command=lambda v: self.config.set("productivity_detect_profile", v)).pack(side="left", padx=5)

        # Custom app rules
        ctk.CTkLabel(tab, text="Custom App Rules", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(5, 2), anchor="w")
        ctk.CTkLabel(tab, text="Map specific apps to profiles (e.g., vlc.exe to Cinema)",
                      text_color="gray", font=ctk.CTkFont(size=11)).pack(padx=20, anchor="w")

        self._app_rules_frame = ctk.CTkScrollableFrame(tab, height=150)
        self._app_rules_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self._app_rule_widgets = []
        rules = self.config.get("app_rules", [])
        for rule in rules:
            self._add_app_rule_row(rule.get("exe", ""), rule.get("profile", "Work"))

        btnf = ctk.CTkFrame(tab, fg_color="transparent")
        btnf.pack(padx=10, pady=2, fill="x")
        ctk.CTkButton(btnf, text="+ Add Rule", width=100,
                       command=lambda: self._add_app_rule_row("", "Work")).pack(side="left", padx=5)
        ctk.CTkButton(btnf, text="Save Rules", width=100,
                       command=self._save_app_rules).pack(side="left", padx=5)

        self._app_rules_status = ctk.CTkLabel(tab, text="", text_color="gray")
        self._app_rules_status.pack(padx=15, anchor="w")

        # Game database info
        def show_game_count():
            from appdetect import _known_game_exes, _games_scanned
            if _games_scanned:
                self._app_rules_status.configure(
                    text=f"Known games database: {len(_known_game_exes)} game(s) detected")
            else:
                self._app_rules_status.configure(text="Game database still loading...")

        ctk.CTkButton(tab, text="Show Detected Games Count", width=180,
                       command=show_game_count).pack(padx=10, pady=(2, 5), anchor="w")

    def _add_app_rule_row(self, exe_name, profile_name):
        """Add an app rule row."""
        row = ctk.CTkFrame(self._app_rules_frame, fg_color="transparent")
        row.pack(fill="x", padx=5, pady=2)

        exe_var = ctk.StringVar(value=exe_name)
        ctk.CTkEntry(row, textvariable=exe_var, width=180,
                      placeholder_text="app.exe").pack(side="left", padx=5)

        profile_var = ctk.StringVar(value=profile_name)
        names = self.pm.get_profile_names()
        ctk.CTkOptionMenu(row, values=names, variable=profile_var,
                           width=120).pack(side="left", padx=5)

        def remove():
            row.destroy()
            self._app_rule_widgets = [(e, p, r) for e, p, r in self._app_rule_widgets if r != row]

        ctk.CTkButton(row, text="X", width=30, fg_color="firebrick",
                       command=remove).pack(side="left", padx=5)

        self._app_rule_widgets.append((exe_var, profile_var, row))

    def _save_app_rules(self):
        """Save app rules to config."""
        rules = []
        for exe_var, profile_var, row in self._app_rule_widgets:
            if row.winfo_exists():
                exe = exe_var.get().strip()
                profile = profile_var.get()
                if exe and profile:
                    rules.append({"exe": exe, "profile": profile})
        self.config.set("app_rules", rules)
        if hasattr(self, '_app_detector') and self._app_detector:
            self._app_detector.reload()
        self._app_rules_status.configure(text=f"Saved {len(rules)} rule(s)")

    # ── General Tab ────────────────────────────────────────

    def _build_general_tab(self, tab):
        # Auto-start
        self._autostart_var = ctk.BooleanVar(value=self.config.get("auto_start", False))
        ctk.CTkSwitch(
            tab, text="Start with Windows",
            variable=self._autostart_var,
            command=self._on_autostart_toggle
        ).pack(padx=15, pady=(10, 3), anchor="w")

        # Notifications
        self._notif_var = ctk.BooleanVar(value=self.config.get("notifications_enabled", True))
        ctk.CTkSwitch(
            tab, text="Show notifications on profile switch",
            variable=self._notif_var,
            command=lambda: self.config.set("notifications_enabled", self._notif_var.get())
        ).pack(padx=15, pady=3, anchor="w")

        # Ambient mode
        self._ambient_var = ctk.BooleanVar(value=self.config.get("ambient_mode", False))
        ctk.CTkSwitch(
            tab, text="Ambient mode (gradual colour shift with sun)",
            variable=self._ambient_var,
            command=lambda: self.config.set("ambient_mode", self._ambient_var.get())
        ).pack(padx=15, pady=3, anchor="w")

        # Language
        lf = ctk.CTkFrame(tab, fg_color="transparent")
        lf.pack(padx=10, pady=(5, 3), fill="x")
        ctk.CTkLabel(lf, text="Language:").pack(side="left", padx=5)
        from i18n import get_available_languages, load_language, get_current_language
        langs = get_available_languages()
        lang_names = [name for code, name in langs]
        lang_codes = [code for code, name in langs]
        current_code = self.config.get("language", "en")
        current_name = next((name for code, name in langs if code == current_code), "English")
        self._lang_var = ctk.StringVar(value=current_name)

        def on_lang_change(name):
            idx = lang_names.index(name) if name in lang_names else 0
            code = lang_codes[idx]
            self.config.set("language", code)
            load_language(code)
            self._lang_status.configure(text=f"Language set to {name} — restart app to apply fully")

        ctk.CTkOptionMenu(lf, values=lang_names, variable=self._lang_var,
                           width=140, command=on_lang_change).pack(side="left", padx=5)
        self._lang_status = ctk.CTkLabel(lf, text="", text_color="gray", font=ctk.CTkFont(size=11))
        self._lang_status.pack(side="left", padx=5)

        # Transition speed
        ctk.CTkLabel(tab, text="Transition Speed", anchor="w").pack(padx=15, pady=(8, 0), anchor="w")
        tf = ctk.CTkFrame(tab, fg_color="transparent")
        tf.pack(padx=10, fill="x")

        self._transition_var = ctk.IntVar(value=self.config.get("transition_ms", 0))
        self._transition_label = ctk.CTkLabel(tf, text=self._format_transition(self.config.get("transition_ms", 0)), width=80)
        self._transition_label.pack(side="right", padx=5)
        ctk.CTkSlider(
            tf, from_=0, to=2000, variable=self._transition_var,
            command=self._on_transition_change
        ).pack(side="left", fill="x", expand=True, padx=5)

        # Hotkey info
        ctk.CTkLabel(tab, text="Hotkeys", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(8, 2), anchor="w")

        hotkey_info = (
            "Profiles: Ctrl+Alt+1/2/3/4\n"
            "Quick Dim: Ctrl+Alt+D    Lock: Ctrl+Alt+L\n"
            "Panic (Work): Ctrl+Alt+P    Disco: Ctrl+Alt+Shift+D\n"
            "Brightness: Ctrl+Alt+Shift+Up/Down (±5%), PgUp/PgDn (±15%)\n"
            "Colour Temp: Ctrl+Alt+Shift+Left/Right (±200K)"
        )
        ctk.CTkLabel(tab, text=hotkey_info, justify="left", anchor="w",
                      text_color="gray", font=ctk.CTkFont(size=12)).pack(padx=20, anchor="w")

        # Status display
        ctk.CTkLabel(tab, text="Current Status", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(8, 2), anchor="w")

        self._status_frame = ctk.CTkFrame(tab)
        self._status_frame.pack(padx=10, pady=2, fill="x")

        self._status_label = ctk.CTkLabel(
            self._status_frame, text=self._get_status_text(),
            justify="left", anchor="w"
        )
        self._status_label.pack(padx=15, pady=6, anchor="w")

        ctk.CTkButton(tab, text="Refresh Status", width=120,
                       command=self._refresh_status).pack(padx=10, pady=3, anchor="w")

        # Version
        ctk.CTkLabel(tab, text="v1.1 — see About tab for more",
                      text_color="gray", font=ctk.CTkFont(size=11)).pack(padx=15, pady=(3, 0), anchor="w")

    def _open_donate(self):
        import webbrowser
        webbrowser.open("https://buymeacoffee.com/mousewheeldigital")

    def _on_autostart_toggle(self):
        enabled = self._autostart_var.get()
        self.config.set("auto_start", enabled)
        autostart.sync_autostart(self.config)

    def _on_transition_change(self, value):
        ms = int(value)
        self._transition_label.configure(text=self._format_transition(ms))
        self.config.set("transition_ms", ms)

    def _format_transition(self, ms):
        if ms == 0:
            return "Instant"
        return f"{ms}ms"

    def _get_status_text(self):
        active = self.pm.get_active()
        brightness = display.get_brightness()
        kelvin = display.get_colour_temperature()
        refresh = display.get_refresh_rate()
        monitors = display.get_monitor_count()
        locked = self.pm.is_locked()
        dimmed = display.is_dimmed()
        ambient = self.config.get("ambient_mode", False)
        b_str = f"{brightness}%" if brightness is not None else "Unknown"
        r_str = f"{refresh} Hz" if refresh else "Unknown"
        lock_str = " [LOCKED]" if locked else ""
        dim_str = " [DIMMED]" if dimmed else ""
        amb_str = " [AMBIENT]" if ambient else ""
        mon_str = f"{monitors} monitor(s)" if monitors > 1 else "1 monitor"
        return f"Profile: {active}{lock_str}{dim_str}{amb_str}\nBrightness: {b_str}\nColour Temp: {kelvin}K\nRefresh Rate: {r_str}\nMonitors: {mon_str}"

    def _refresh_status(self):
        self._status_label.configure(text=self._get_status_text())

    # ── Stats Tab ──────────────────────────────────────────

    def _build_stats_tab(self, tab):
        ctk.CTkLabel(tab, text="Usage Stats", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(10, 5), anchor="w")

        # Today
        ctk.CTkLabel(tab, text="Today", anchor="w").pack(padx=15, pady=(5, 2), anchor="w")
        self._today_stats_frame = ctk.CTkFrame(tab)
        self._today_stats_frame.pack(padx=10, pady=2, fill="x")

        # This week
        ctk.CTkLabel(tab, text="This Week", anchor="w").pack(padx=15, pady=(10, 2), anchor="w")
        self._week_stats_frame = ctk.CTkFrame(tab)
        self._week_stats_frame.pack(padx=10, pady=2, fill="x")

        ctk.CTkButton(tab, text="Refresh Stats", width=120,
                       command=self._refresh_stats).pack(padx=10, pady=10, anchor="w")

        self._refresh_stats()

    def _refresh_stats(self):
        """Refresh the stats display with bar charts."""
        if not self.stats:
            return

        # Profile colours for bars
        bar_colours = {
            "Work": "#508CFF",
            "Code": "#FFB432",
            "Game": "#32C850",
            "Cinema": "#B43CB4",
        }
        default_bar = "#6496FF"

        # Today
        for widget in self._today_stats_frame.winfo_children():
            widget.destroy()
        today = self.stats.get_today_stats()
        self._draw_stat_bars(self._today_stats_frame, today, bar_colours, default_bar)

        # Week
        for widget in self._week_stats_frame.winfo_children():
            widget.destroy()
        week = self.stats.get_week_stats()
        self._draw_stat_bars(self._week_stats_frame, week, bar_colours, default_bar)

    def _draw_stat_bars(self, parent, data, colours, default_colour):
        """Draw horizontal bar chart for stats data."""
        if not data:
            ctk.CTkLabel(parent, text="No data yet", text_color="gray").pack(padx=15, pady=8)
            return

        max_val = max(data.values()) if data else 1
        for profile, seconds in sorted(data.items(), key=lambda x: -x[1]):
            row = ctk.CTkFrame(parent, fg_color="transparent")
            row.pack(fill="x", padx=10, pady=2)

            # Label
            duration = self.stats.format_duration(seconds)
            ctk.CTkLabel(row, text=f"{profile}", width=60, anchor="w").pack(side="left")

            # Bar
            bar_width = max(10, int(250 * seconds / max_val)) if max_val > 0 else 10
            colour = colours.get(profile, default_colour)
            bar = ctk.CTkFrame(row, height=18, width=bar_width, fg_color=colour, corner_radius=4)
            bar.pack(side="left", padx=5)
            bar.pack_propagate(False)

            # Duration text
            ctk.CTkLabel(row, text=duration, text_color="gray", width=60).pack(side="left", padx=5)

    # ── About Tab ──────────────────────────────────────────

    def _build_about_tab(self, tab):
        from pathlib import Path
        from PIL import Image, ImageTk

        # Logo
        logo_path = Path(__file__).parent.parent / "assets" / "mousewheel_logo.png"
        try:
            if logo_path.exists():
                logo = Image.open(str(logo_path)).convert("RGBA")
                logo = logo.resize((80, 80), Image.LANCZOS)
                self._about_logo_img = ImageTk.PhotoImage(logo)
                ctk.CTkLabel(tab, image=self._about_logo_img, text="").pack(pady=(20, 5))
        except Exception:
            pass

        # App name and version
        ctk.CTkLabel(tab, text="Display Manager",
                      font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(5, 0))
        ctk.CTkLabel(tab, text="Version 1.1",
                      text_color="gray", font=ctk.CTkFont(size=13)).pack(pady=(0, 5))

        # Branding
        ctk.CTkLabel(tab, text="A MouseWheel Digital product",
                      font=ctk.CTkFont(size=13)).pack(pady=(5, 0))
        ctk.CTkLabel(tab, text="Digital products. Built with purpose.",
                      text_color="gray", font=ctk.CTkFont(size=11, slant="italic")).pack(pady=(0, 10))

        # Links frame
        links = ctk.CTkFrame(tab, fg_color="transparent")
        links.pack(pady=5)

        ctk.CTkButton(links, text="mousewheeldigital.com", width=180,
                       fg_color="transparent", border_width=1, border_color="gray",
                       command=lambda: __import__("webbrowser").open(
                           "https://www.mousewheeldigital.com/")).pack(pady=3)

        ctk.CTkButton(links, text="Buy Me a Coffee", width=180,
                       fg_color="#FFDD00", text_color="black",
                       command=self._open_donate).pack(pady=3)

        # Feedback
        ctk.CTkLabel(tab, text="Feedback & Support", anchor="w",
                      font=ctk.CTkFont(weight="bold")).pack(padx=15, pady=(15, 2), anchor="w")

        feedback_frame = ctk.CTkFrame(tab, fg_color="transparent")
        feedback_frame.pack(padx=15, anchor="w")
        ctk.CTkLabel(feedback_frame, text="feedback@mousewheeldigital.com",
                      font=ctk.CTkFont(size=12)).pack(side="left")
        ctk.CTkButton(feedback_frame, text="Copy", width=50, height=24,
                       fg_color="gray30",
                       command=self._copy_feedback_email).pack(side="left", padx=8)

        # GitHub
        ctk.CTkButton(tab, text="GitHub: MorlachAU/DisplayManager", width=240,
                       fg_color="transparent", border_width=1, border_color="gray",
                       command=lambda: __import__("webbrowser").open(
                           "https://github.com/MorlachAU/DisplayManager")).pack(pady=(10, 5))

        # Credits
        ctk.CTkLabel(tab, text="Built with the assistance of Claude Code by Anthropic",
                      text_color="gray", font=ctk.CTkFont(size=10)).pack(pady=(10, 5))

    def _copy_feedback_email(self):
        """Copy feedback email to clipboard."""
        if self._root:
            self._root.clipboard_clear()
            self._root.clipboard_append("feedback@mousewheeldigital.com")
