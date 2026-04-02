"""
Display Manager — Stats Tracker
Tracks time spent in each profile per day.
"""

import threading
import time
import datetime


class StatsTracker:
    def __init__(self, config):
        self.config = config
        self._lock = threading.Lock()
        self._current_profile = config.get_active_profile()
        self._session_start = time.time()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        """Start the stats tracking thread (saves every 60s)."""
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop tracking and save final session."""
        self._stop_event.set()
        self._save_session()

    def on_profile_switch(self, new_profile):
        """Called when profile changes. Saves time for old profile."""
        with self._lock:
            self._save_session()
            self._current_profile = new_profile
            self._session_start = time.time()

    def _save_session(self):
        """Save accumulated time for the current profile."""
        elapsed = time.time() - self._session_start
        if elapsed < 5:  # ignore very short sessions
            return

        today = datetime.date.today().isoformat()
        stats = self.config.get("stats", {})
        if today not in stats:
            stats[today] = {}
        day_stats = stats[today]

        profile = self._current_profile
        day_stats[profile] = day_stats.get(profile, 0) + int(elapsed)

        # Keep only last 30 days
        cutoff = (datetime.date.today() - datetime.timedelta(days=30)).isoformat()
        stats = {k: v for k, v in stats.items() if k >= cutoff}

        self.config.set("stats", stats)
        self._session_start = time.time()

    def _run_loop(self):
        """Periodically save stats."""
        while not self._stop_event.is_set():
            self._stop_event.wait(60)
            if not self._stop_event.is_set():
                with self._lock:
                    self._save_session()

    def get_today_stats(self):
        """Return today's stats as {profile: seconds}."""
        today = datetime.date.today().isoformat()
        stats = self.config.get("stats", {})
        return stats.get(today, {})

    def get_week_stats(self):
        """Return this week's stats as {profile: seconds}."""
        stats = self.config.get("stats", {})
        week_ago = (datetime.date.today() - datetime.timedelta(days=7)).isoformat()
        totals = {}
        for date_str, day_stats in stats.items():
            if date_str >= week_ago:
                for profile, seconds in day_stats.items():
                    totals[profile] = totals.get(profile, 0) + seconds
        return totals

    def format_duration(self, seconds):
        """Format seconds into human-readable duration."""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
