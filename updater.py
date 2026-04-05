"""
Display Manager — Update Checker
Checks GitHub releases for new versions on startup.
"""

import threading
import urllib.request
import json

CURRENT_VERSION = "1.1"
GITHUB_REPO = "MorlachAU/DisplayManager"
RELEASES_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


def _parse_version(version_str):
    """Parse version string like '1.0' or 'v1.2.3' into a tuple of ints."""
    v = version_str.strip().lstrip("v")
    try:
        return tuple(int(x) for x in v.split("."))
    except ValueError:
        return (0,)


def check_for_update(callback):
    """Check GitHub for a newer release. Runs in a background thread.
    Calls callback(version, url) if update available, or callback(None, None) if not."""

    def do_check():
        try:
            req = urllib.request.Request(
                RELEASES_URL,
                headers={"User-Agent": "DisplayManager-UpdateCheck"}
            )
            response = urllib.request.urlopen(req, timeout=10)
            data = json.loads(response.read().decode())

            latest_tag = data.get("tag_name", "")
            latest_version = _parse_version(latest_tag)
            current_version = _parse_version(CURRENT_VERSION)

            if latest_version > current_version:
                release_url = data.get("html_url", f"https://github.com/{GITHUB_REPO}/releases")
                callback(latest_tag, release_url)
            else:
                callback(None, None)
        except Exception:
            # Network error, no internet, etc — fail silently
            callback(None, None)

    threading.Thread(target=do_check, daemon=True).start()
