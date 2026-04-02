"""
Display Manager — Internationalization (i18n)
Simple JSON-based translation system.
"""

import json
import os
from pathlib import Path

_current_lang = {}
_lang_code = "en"
_lang_dir = Path(__file__).parent / "lang"


def get_available_languages():
    """Return list of (code, display_name) for all available languages."""
    languages = []
    if _lang_dir.exists():
        for f in sorted(_lang_dir.glob("*.json")):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                meta = data.get("_meta", {})
                code = meta.get("code", f.stem)
                name = meta.get("language", f.stem)
                languages.append((code, name))
            except Exception:
                pass
    return languages


def load_language(code):
    """Load a language file by code (e.g., 'en', 'de', 'ja')."""
    global _current_lang, _lang_code
    lang_file = _lang_dir / f"{code}.json"
    if not lang_file.exists():
        lang_file = _lang_dir / "en.json"
        code = "en"
    try:
        with open(lang_file, "r", encoding="utf-8") as f:
            _current_lang = json.load(f)
        _lang_code = code
    except Exception:
        _current_lang = {}
        _lang_code = "en"


def t(key, **kwargs):
    """Get a translated string by dot-notation key (e.g., 'tray.quit').
    Supports {placeholder} formatting with kwargs."""
    parts = key.split(".")
    value = _current_lang
    for part in parts:
        if isinstance(value, dict):
            value = value.get(part, None)
        else:
            value = None
        if value is None:
            return key  # fallback: return the key itself
    if isinstance(value, str) and kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value if isinstance(value, str) else key


def get_current_language():
    """Return the current language code."""
    return _lang_code


# Load English by default
load_language("en")
