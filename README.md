# Display Manager

A Windows system tray application that manages display brightness, colour temperature, and refresh rate across switchable profiles. Think of it as a smart display profile manager — set up your preferred screen settings for different activities and switch between them instantly.

Built for anyone who switches between work, coding, and gaming on the same monitor and wants their display to adapt automatically.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-blue)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Features

### Core
- **Three display profiles** — Work, Code, and Game, each with independent settings
- **Brightness control** — DDC/CI hardware backlight adjustment (not software dimming)
- **Colour temperature** — Direct gamma ramp control from 1200K (warm amber) to 6500K (neutral daylight)
- **Refresh rate switching** — Change monitor refresh rate per profile (e.g., 60Hz for work, 100Hz+ for gaming)
- **System tray app** — Minimal footprint, always one click away

### Automation
- **Global hotkeys** — Ctrl+Alt+1/2/3 for instant profile switching (configurable)
- **Sunrise/sunset auto-switching** — Automatically shifts to a warm profile at sunset and back at sunrise, based on your location
- **Time-based scheduling** — Set fixed times to switch profiles (e.g., Work at 8am, Code at 6pm)
- **Monitor wake recovery** — Automatically re-applies your profile when the display wakes from sleep

### Extras
- **Quick Dim** — Ctrl+Alt+D instantly drops brightness to 10% and back
- **Profile Lock** — Ctrl+Alt+L prevents scheduled switches from interrupting your gaming session
- **Per-profile tray icon colours** — Blue (Work), Amber (Code), Green (Game) so you know the active mode at a glance
- **Colour-coded lock indicator** — Red dot on the tray icon when profile lock is active
- **IP-based location detection** — One-click setup for sunrise/sunset feature
- **First-run system check** — Verifies DDC/CI, detects conflicts (f.lux), shows available refresh rates
- **Auto-start with Windows** — Toggle in settings, managed via registry

---

## Requirements

- **Windows 10 or 11**
- A monitor that supports **DDC/CI** (most external monitors made after 2010)
  - DDC/CI must be enabled in your monitor's OSD settings
  - Laptop built-in screens typically do not support DDC/CI
- **f.lux must be closed** if installed — Display Manager replaces f.lux for colour temperature control

---

## Installation

### Option A: Download the release (no Python needed)

1. Download the latest release from [Releases](../../releases)
2. Extract the zip to a folder of your choice
3. Run `DisplayManager.exe`
4. The first-run dialog will check your system and guide you through setup

### Option B: Run from source

1. Clone this repository
2. Install Python 3.10+
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run:
   ```
   pythonw main.py
   ```

---

## Usage

### Switching Profiles

| Method | Action |
|--------|--------|
| **Tray menu** | Right-click the tray icon, click a profile name |
| **Hotkey** | Ctrl+Alt+1 (Work), Ctrl+Alt+2 (Code), Ctrl+Alt+3 (Game) |
| **Schedule** | Automatic — configure in Settings > Schedule |

### Hotkeys

| Hotkey | Action |
|--------|--------|
| Ctrl+Alt+1 | Switch to Work profile |
| Ctrl+Alt+2 | Switch to Code profile |
| Ctrl+Alt+3 | Switch to Game profile |
| Ctrl+Alt+D | Quick Dim toggle (10% brightness) |
| Ctrl+Alt+L | Profile Lock toggle |

Profile hotkeys are configurable in Settings > Profiles.

### Settings

Right-click the tray icon and click **Settings** to open the configuration window:

- **Profiles tab** — Adjust brightness, colour temperature, refresh rate, and hotkey for each profile. Use "Revert to Default" to reset a profile.
- **Schedule tab** — Enable sunrise/sunset auto-switching (click "Detect" to set your location automatically) or add fixed time rules.
- **General tab** — Auto-start toggle, transition speed, hotkey reference, and current status display.

### Profile Lock

When gaming, you don't want a scheduled switch interrupting you. Press **Ctrl+Alt+L** or right-click the tray icon and click "Lock Profile". While locked:
- Scheduled and sunrise/sunset switches are blocked
- Manual switches (hotkey or tray menu) still work
- A red dot appears on the tray icon as a reminder
- Unlock the same way, or it resets on next app launch

---

## Default Profiles

| Profile | Brightness | Colour Temp | Refresh Rate | Use Case |
|---------|-----------|-------------|-------------|----------|
| **Work** | 80% | 6500K (neutral) | 60 Hz | Documents, dashboards, video calls |
| **Code** | 50% | 5000K (warm) | 60 Hz | Dark theme coding, evening sessions |
| **Game** | 75% | 6500K (neutral) | 100 Hz | Colour accuracy, smooth gameplay |

All values are fully customisable per profile.

---

## How It Works

| Feature | Technology |
|---------|-----------|
| Brightness | DDC/CI via [monitorcontrol](https://github.com/newAM/monitorcontrol) — hardware backlight, not software overlay |
| Colour temperature | Win32 `SetDeviceGammaRamp` — same technique f.lux uses internally |
| Refresh rate | Win32 `ChangeDisplaySettingsW` — system-level display mode change |
| Sunrise/sunset | [astral](https://github.com/sffjunkie/astral) library — offline calculation, no internet needed after location is set |
| System tray | [pystray](https://github.com/moses-palmer/pystray) |
| Settings UI | [customtkinter](https://github.com/TomSchimansky/CustomTkinter) |
| Global hotkeys | [keyboard](https://github.com/boppreh/keyboard) |

---

## Configuration

Settings are stored in `config.json` alongside the executable (or `main.py` if running from source). The file is created automatically on first run with sensible defaults. You can edit it directly, but the Settings UI is the intended way to configure everything.

---

## Troubleshooting

**"No DDC/CI monitor found"**
- Check that DDC/CI is enabled in your monitor's OSD (on-screen display) settings
- Laptop screens don't support DDC/CI — this app is designed for external monitors
- Try a different cable — some cheap HDMI cables don't carry DDC/CI signals

**Colour temperature reverts immediately**
- f.lux is probably running — close it. Both apps write the same gamma ramp and will fight each other.

**Brightness doesn't change**
- Some monitors have a DDC/CI setting buried in a submenu — check your monitor manual
- Try disconnecting and reconnecting the display cable

**Tray icon not visible**
- Click the "^" overflow arrow in the Windows taskbar — new tray icons are often hidden there
- Drag the icon out of overflow to pin it to the taskbar

---

## Building from Source

To create a standalone executable:

```
pip install pyinstaller
pyinstaller --noconfirm --windowed --name "DisplayManager" --icon "assets/icon.ico" --add-data "assets;assets" --collect-all customtkinter --hidden-import pystray._win32 main.py
```

The output will be in `dist/DisplayManager/`. Zip the entire folder to distribute.

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Credits

Built with the assistance of [Claude Code](https://claude.ai/code) by Anthropic.
