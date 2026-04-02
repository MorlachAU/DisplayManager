"""
Display Manager — Time-Based Scheduler
Switches profiles based on fixed times or sunrise/sunset.
"""

import threading
import datetime
import schedule
import display

try:
    from astral import LocationInfo
    from astral.sun import sun
    HAS_ASTRAL = True
except ImportError:
    HAS_ASTRAL = False


class ScheduleManager:
    def __init__(self, profile_manager, config):
        self.pm = profile_manager
        self.config = config
        self._stop_event = threading.Event()
        self._thread = None
        self._last_sun_check_date = None
        self._sunrise_time = None
        self._sunset_time = None
        self._sun_switched_today = {"sunrise": False, "sunset": False}

    def start(self):
        """Load schedule rules and start the polling thread."""
        self._load_rules()
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the scheduler thread."""
        self._stop_event.set()
        schedule.clear()

    def reload(self):
        """Reload rules from config."""
        schedule.clear()
        self._last_sun_check_date = None
        self._sun_switched_today = {"sunrise": False, "sunset": False}
        self._load_rules()

    def _load_rules(self):
        """Register fixed schedule rules from config."""
        if not self.config.get("schedule_enabled", False):
            return
        rules = self.config.get_schedule_rules()
        for rule in rules:
            time_str = rule.get("time", "")
            profile = rule.get("profile", "")
            if time_str and profile:
                try:
                    schedule.every().day.at(time_str).do(self.pm.switch, profile)
                except Exception:
                    pass

    def _update_sun_times(self):
        """Calculate today's sunrise and sunset times."""
        if not HAS_ASTRAL:
            return

        sun_config = self.config.get("sun_schedule", {})
        if not sun_config.get("enabled", False):
            return

        today = datetime.date.today()
        if self._last_sun_check_date == today:
            return

        lat = sun_config.get("latitude", -35.26)
        lon = sun_config.get("longitude", 138.89)

        try:
            loc = LocationInfo(latitude=lat, longitude=lon)
            s = sun(loc.observer, date=today)
            self._sunrise_time = s["sunrise"].astimezone().replace(tzinfo=None)
            self._sunset_time = s["sunset"].astimezone().replace(tzinfo=None)
            self._last_sun_check_date = today
            self._sun_switched_today = {"sunrise": False, "sunset": False}
        except Exception:
            pass

    def _check_sun_schedule(self):
        """Check if we should switch based on sunrise/sunset."""
        sun_config = self.config.get("sun_schedule", {})
        if not sun_config.get("enabled", False):
            return

        self._update_sun_times()
        if self._sunrise_time is None or self._sunset_time is None:
            return

        now = datetime.datetime.now()

        # Check sunrise
        if (not self._sun_switched_today["sunrise"]
                and self._sunrise_time <= now
                and now < self._sunrise_time + datetime.timedelta(minutes=2)):
            profile = sun_config.get("sunrise_profile", "Work")
            self.pm.switch(profile)
            self._sun_switched_today["sunrise"] = True

        # Check sunset
        if (not self._sun_switched_today["sunset"]
                and self._sunset_time <= now
                and now < self._sunset_time + datetime.timedelta(minutes=2)):
            profile = sun_config.get("sunset_profile", "Code")
            self.pm.switch(profile)
            self._sun_switched_today["sunset"] = True

    def get_sun_times(self):
        """Return today's sunrise/sunset as strings. For display in UI."""
        self._update_sun_times()
        if self._sunrise_time and self._sunset_time:
            return (self._sunrise_time.strftime("%H:%M"),
                    self._sunset_time.strftime("%H:%M"))
        return None, None

    def _apply_ambient_mode(self):
        """Gradually shift colour temperature based on time of day relative to sun position."""
        if not self.config.get("ambient_mode", False):
            return
        if self.config.get("profile_lock", False):
            return
        if not HAS_ASTRAL:
            return

        self._update_sun_times()
        if self._sunrise_time is None or self._sunset_time is None:
            return

        import display
        now = datetime.datetime.now()

        # Calculate target colour temp based on sun position
        # Sunrise -> noon: 5000K -> 6500K
        # Noon -> sunset: 6500K -> 5000K
        # Sunset -> sunset+2h: 5000K -> 3500K
        # Night (after sunset+2h): 3500K
        # Before sunrise: 3500K

        sunrise = self._sunrise_time
        sunset = self._sunset_time
        noon = sunrise + (sunset - sunrise) / 2
        evening_end = sunset + datetime.timedelta(hours=2)

        if now < sunrise:
            target_k = 3500
        elif now < noon:
            # Morning warming up
            progress = (now - sunrise).total_seconds() / (noon - sunrise).total_seconds()
            target_k = int(5000 + progress * 1500)
        elif now < sunset:
            # Afternoon cooling down
            progress = (now - noon).total_seconds() / (sunset - noon).total_seconds()
            target_k = int(6500 - progress * 1500)
        elif now < evening_end:
            # Evening dimming
            progress = (now - sunset).total_seconds() / (evening_end - sunset).total_seconds()
            target_k = int(5000 - progress * 1500)
        else:
            target_k = 3500

        target_k = max(3500, min(6500, target_k))

        # Only adjust if the difference is noticeable (>100K)
        current_k = display.get_colour_temperature()
        if abs(current_k - target_k) > 100:
            display.set_colour_temperature(target_k)

    def get_ambient_temp(self):
        """Return what colour temp ambient mode would set right now."""
        # Used by UI to display current ambient target
        return display.get_colour_temperature() if self.config.get("ambient_mode", False) else None

    def _run_loop(self):
        """Poll loop — runs pending jobs, sun checks, and ambient mode every 60 seconds."""
        while not self._stop_event.is_set():
            if self.config.get("schedule_enabled", False):
                schedule.run_pending()
            self._check_sun_schedule()
            self._apply_ambient_mode()
            self._stop_event.wait(60)
