<p align="center">
  <img src="assets/banner.png" alt="Display Manager by MouseWheel Digital" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%2F11-blue" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
  <img src="https://img.shields.io/badge/MouseWheel_Digital-Product-00c8a0" alt="MouseWheel Digital">
</p>

# Display Manager

A Windows system tray application that manages display brightness, colour temperature, and refresh rate across switchable profiles. Think of it as a smart display profile manager — set up your preferred screen settings for different activities and switch between them instantly.

Built for anyone who switches between work, coding, and gaming on the same monitor and wants their display to adapt automatically.

---

## Features

### Core
- **Four display profiles** — Work, Code, Game, and Cinema, each with independent settings
- **Multi-monitor support** — Automatically detects and controls all connected displays
- **Brightness control** — Hardware backlight adjustment via DDC/CI (external monitors) and WMI (laptop screens)
- **Colour temperature** — Direct gamma ramp control from 1200K (warm amber) to 6500K (neutral daylight)
- **Refresh rate switching** — Change monitor refresh rate per profile (e.g., 60Hz for work, 100Hz+ for gaming)
- **System tray app** — Minimal footprint, always one click away

### Automation
- **App-aware profile switching** — Automatically detects games and switches to your Game profile. Uses four detection layers: Windows game registry, Steam/Epic library scanning, fullscreen detection, and DirectX/Vulkan DLL analysis. Works with any GPU (NVIDIA, AMD, Intel). Reverts when you close the game.
- **Custom app rules** — Map any application to any profile (e.g., VLC → Cinema, VS Code → Code)
- **Global hotkeys** — Ctrl+Alt+1/2/3/4 for instant profile switching (configurable)
- **Ambient mode** — Colour temperature gradually shifts throughout the day following the sun's position (warm at night, neutral at noon)
- **Sunrise/sunset auto-switching** — Automatically shifts to a configured profile at sunset and sunrise
- **Time-based scheduling** — Set fixed times to switch profiles (e.g., Work at 8am, Code at 6pm)
- **Monitor wake recovery** — Automatically re-applies your profile when the display wakes from sleep

### Extras
- **Cinema mode** — A dedicated profile for movie watching (30% brightness, 3500K warm, purple tray icon)
- **Panic button** — Ctrl+Alt+P instantly switches to Work mode (for when the boss walks in)
- **Quick Dim** — Ctrl+Alt+D instantly drops brightness to 10% and back
- **Profile Lock** — Ctrl+Alt+L prevents scheduled switches from interrupting your gaming session
- **Disco mode** — Ctrl+Alt+Shift+D for 5 seconds of wild colour cycling (easter egg)
- **Usage stats** — Track hours spent in each profile per day/week with visual bar charts
- **Notification toasts** — Windows notifications on profile switch (toggle-able)
- **Per-profile tray icon colours** — Blue (Work), Amber (Code), Green (Game), Purple (Cinema)
- **Colour-coded lock indicator** — Red dot on the tray icon when profile lock is active
- **IP-based location detection** — One-click setup for sunrise/sunset feature
- **First-run system check** — Verifies DDC/CI, detects conflicts (f.lux), shows available refresh rates
- **Auto-start with Windows** — Toggle in settings, managed via registry

---

## Requirements

- **Windows 10 or 11**
- Works on **laptops** (built-in screen via WMI) and **external monitors** (via DDC/CI)
  - For external monitors, DDC/CI must be enabled in the monitor's OSD settings
- **f.lux must be closed** if installed — Display Manager replaces f.lux for colour temperature control

---

## Installation

**No additional software required.** Display Manager is fully self-contained — it controls your display directly through Windows APIs. No need to install f.lux, ClickMonitorDDC, Monitorian, or any other display utility.

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
| **Hotkey** | Ctrl+Alt+1 (Work), Ctrl+Alt+2 (Code), Ctrl+Alt+3 (Game), Ctrl+Alt+4 (Cinema) |
| **Schedule** | Automatic — configure in Settings > Schedule |

### Hotkeys

| Hotkey | Action |
|--------|--------|
| Ctrl+Alt+1 | Switch to Work profile |
| Ctrl+Alt+2 | Switch to Code profile |
| Ctrl+Alt+3 | Switch to Game profile |
| Ctrl+Alt+4 | Switch to Cinema profile |
| Ctrl+Alt+D | Quick Dim toggle (10% brightness) |
| Ctrl+Alt+L | Profile Lock toggle |
| Ctrl+Alt+P | Panic button (instant Work mode) |
| Ctrl+Alt+Shift+D | Disco mode (5 second easter egg) |

Profile hotkeys are configurable in Settings > Profiles.

### Settings

Right-click the tray icon and click **Settings** to open the configuration window:

- **Profiles tab** — Adjust brightness, colour temperature, refresh rate, and hotkey for each profile. Use "Revert to Default" to reset a profile.
- **Schedule tab** — Enable sunrise/sunset auto-switching (click "Detect" to set your location automatically) or add fixed time rules.
- **Apps tab** — Configure app-aware switching. Auto-detects games, or add custom rules to map any app to a profile. Choose which profile games switch to.
- **General tab** — Auto-start, notifications, ambient mode, transition speed, hotkey reference, and current status.
- **Stats tab** — Visual bar charts showing time spent in each profile today and this week.

### Profile Lock (Auto-Lock)

When you manually select a profile (tray menu or hotkey), it **automatically locks** to prevent scheduled or ambient switches from overriding your choice. You'll see a red dot on the tray icon confirming the lock.

To return to automatic mode, either:
- Right-click the tray icon and click **Unlock Profile**
- Press **Ctrl+Alt+L**
- Select **Ambient** from the tray menu (auto-unlocks and enables ambient mode)

While locked:
- Scheduled, sunrise/sunset, and ambient switches are all blocked
- Manual switches (hotkey or tray menu) still work
- Lock resets on next app launch

### Ambient Mode

Ambient mode gradually shifts colour temperature throughout the day following the sun's position — warm at night, neutral around noon. It's like f.lux but built in.

Right-click the tray icon and select **Ambient** to enable it (shows a checkmark when active). Ambient appears alongside the profiles in the tray menu, so you can quickly switch between a fixed profile and ambient mode.

Selecting a fixed profile (Work, Code, Game, Cinema) auto-locks and disables ambient adjustments. Selecting Ambient unlocks and lets the automatic colour shifting resume.

---

## Default Profiles

| Profile | Brightness | Colour Temp | Refresh Rate | Use Case |
|---------|-----------|-------------|-------------|----------|
| **Work** | 80% | 6500K (neutral) | 60 Hz | Documents, dashboards, video calls |
| **Code** | 50% | 5000K (warm) | 60 Hz | Dark theme coding, evening sessions |
| **Game** | 75% | 6500K (neutral) | 100 Hz | Colour accuracy, smooth gameplay |
| **Cinema** | 30% | 3500K (warm) | No change | Movie watching, cosy vibes |

All values are fully customisable per profile.

---

## How It Works

| Feature | Technology |
|---------|-----------|
| Brightness | [screen-brightness-control](https://github.com/Crozzers/screen-brightness-control) — DDC/CI for external monitors, WMI for laptops |
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

**"No displays found" or brightness not changing**
- **External monitors:** Check that DDC/CI is enabled in your monitor's OSD settings. Try a different cable — some cheap HDMI cables don't carry DDC/CI signals.
- **Laptops:** Brightness control uses WMI which works on most laptops. If it doesn't work, check your display driver is up to date.

**Colour temperature reverts immediately**
- f.lux is probably running — close it. Both apps write the same gamma ramp and will fight each other.

**Brightness doesn't change**
- Some monitors have a DDC/CI setting buried in a submenu — check your monitor manual
- Try disconnecting and reconnecting the display cable

**Tray icon not visible**
- Click the "^" overflow arrow in the Windows taskbar — new tray icons are often hidden there
- Drag the icon out of overflow to pin it to the taskbar

---

## FAQ

**Do I need any other software to use Display Manager?**
No. Display Manager is completely self-contained and controls your display directly through Windows APIs. You do not need f.lux, Monitorian, Twinkle Tray, ClickMonitorDDC, or any other display utility. If you have f.lux installed, you should close or uninstall it — both apps control the same gamma ramp and will conflict with each other.

**Does it work on laptops?**
Yes. Brightness control works on laptop screens via WMI and on external monitors via DDC/CI. Colour temperature and refresh rate work on all displays.

**What happens if I plug in a second monitor?**
Display Manager detects all connected displays automatically. Brightness changes are applied to all monitors. Restart the app after connecting a new display for it to be detected.

**Why does my screen go black briefly when switching to Game mode?**
This is standard Windows behaviour, not a Display Manager issue. When your profiles use different refresh rates (e.g., 60Hz for Work, 100Hz for Game), Windows performs a full display mode change which momentarily blanks the screen. This happens with any application that changes the refresh rate. Switching between profiles with the same refresh rate is instant with no flash.

**What does the red dot on the tray icon mean?**
Your profile is locked. This happens automatically when you manually select a profile (to prevent scheduled switches from overriding your choice). Right-click the tray icon and click "Unlock Profile" or press Ctrl+Alt+L to return to automatic mode.

**What's the difference between Ambient mode and the sunrise/sunset schedule?**
The sunrise/sunset schedule switches between two fixed profiles at sunrise and sunset. Ambient mode is more gradual — it continuously adjusts colour temperature throughout the day (neutral at noon, warm in the evening, very warm at night) like a smooth curve rather than a hard switch.

**Can I use both Ambient mode and fixed schedules?**
You can, but ambient mode will override the colour temperature set by a scheduled profile switch. For most people, pick one or the other.

**What's Cinema mode for?**
It's a dedicated profile for watching movies or relaxing — low brightness (30%), warm colour temperature (3500K), and it doesn't change the refresh rate. Think of it as "cosy screen" mode.

**What's the Panic button?**
Press Ctrl+Alt+P and it instantly switches to Work mode. Useful for... situations where you need to look productive quickly.

**Is there really a Disco mode?**
Yes. Press Ctrl+Alt+Shift+D for 5 seconds of rapidly cycling colour temperatures. It's an easter egg. Your display settings are restored automatically after it finishes.

**How does game detection work?**
Display Manager uses four detection methods that work with any GPU vendor (NVIDIA, AMD, Intel): (1) Windows GameConfigStore registry — the OS already tracks what it considers a game, (2) Steam and Epic library scanning for installed game executables, (3) fullscreen + borderless window detection, and (4) checking if the foreground process has DirectX or Vulkan rendering DLLs loaded. When a game is detected, it auto-switches to your chosen Game profile. When you close the game, it reverts to whatever profile was active before.

**Can I make it switch profiles for non-game apps too?**
Yes. Go to Settings > Apps and add custom rules. For example, map `vlc.exe` to Cinema or `Code.exe` to Code. Custom rules take priority over game detection.

**Does the app phone home or collect data?**
No. Everything runs locally. The only network call is the optional one-click location detection (via ip-api.com) for setting up sunrise/sunset — and that only happens when you click "Detect" in Settings. Usage stats are stored locally in config.json and never leave your machine.

**What happens if the app crashes?**
On next launch, Display Manager re-applies the last active profile, which resets the gamma ramp to the correct state. If the gamma ramp is stuck from a crash, just restart the app.

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

<p align="center">
  <img src="assets/mousewheel_logo.png" alt="MouseWheel Digital" width="80">
  <br>
  <strong>A <a href="https://www.mousewheeldigital.com/">MouseWheel Digital</a> product</strong>
  <br>
  <em>Digital products. Built with purpose.</em>
  <br><br>
  Built with the assistance of <a href="https://claude.ai/code">Claude Code</a> by Anthropic.
</p>
