# Project brief — BOJANGLES Display Manager

> AI-to-AI handoff document. Written by Claude (claude.ai) for Claude Code.
> Read this fully before writing a single line of code.

---

## Who is Ben?

- IT Manager, ~25 years infrastructure experience (WINTEL, networking, government sectors)
- Highly comfortable with terminals, file systems, and technical concepts
- Not a developer by trade — he's the director, you're the builder
- He goes by Ben. Keep it casual.
- His PC is named **BOJANGLES**, after his late dog Bo

---

## What we're building

A **Windows system tray application** that manages display settings across three named profiles: Work, Code, and Game. Ben switches between these modes daily and wants a single app that handles brightness, colour temperature, and related settings automatically — no manual fiddling.

Think of it as a smart display profile manager that knows what Ben is doing and configures his screen accordingly.

---

## Ben's hardware — know this cold

| Component    | Detail                                                                |
| ------------ | --------------------------------------------------------------------- |
| Machine      | BOJANGLES — Windows 11 Pro Insider Preview (10.0.26220)               |
| CPU          | Intel i7-8700K @ 3.70GHz (12 logical cores)                           |
| RAM          | 32GB                                                                  |
| GPU          | NVIDIA GeForce RTX 3060 Ti (4GB VRAM, driver 32.0.15.9579)            |
| Monitor      | Single ASUS ROG Swift PG349Q — 3440×1440 @ 100Hz                      |
| Refresh      | Variable (G-Sync, 10–100Hz), 8-bit, RGB, SDR                          |
| Monitor ID   | DISPLAY\AUS343B                                                       |
| Keyboard     | Logitech G910                                                         |
| Mouse        | Logitech G903                                                         |
| Headset      | Logitech G733                                                         |
| Network      | NBN FTTP 1000/100Mbps, Aussie Broadband, ASUS GT-AX11000 router, WiFi |
| File manager | Directory Opus (not Windows Explorer)                                 |

**Important:** Windows WMI reports duplicate monitor entries for the PG349Q due to multiple input ports — there is physically only ONE monitor.

---

## The three profiles

| Profile  | When                          | Brightness            | Colour temp             | f.lux                           | Notes                                               |
| -------- | ----------------------------- | --------------------- | ----------------------- | ------------------------------- | --------------------------------------------------- |
| **Work** | Daytime, business hours       | High (~80–100%)       | Neutral / cool          | Minimal warming                 | Document reading, dashboards, Teams calls           |
| **Code** | Evening, Claude Code sessions | Low–medium (~40–60%)  | Warm but not aggressive | Enabled, mild                   | Dark theme coding — too much amber wash looks muddy |
| **Game** | Any time, manual trigger      | Medium–high (~70–85%) | Neutral                 | Disabled / fullscreen exception | Colour accuracy matters in games                    |

These are sensible defaults. The app must allow Ben to customise every value per profile.

---

## How it controls the hardware

### Brightness — ClickMonitorDDC

Controls physical monitor backlight via DDC/CI over the data cable. The PG349Q almost certainly supports DDC/CI — verify this on first run.

```
ClickMonitorDDC.exe b 60        # set brightness to 60%
ClickMonitorDDC.exe b 60 AUS343B  # target specific monitor by ID if needed
```

Download: https://clickmonitorddc.bplaced.net/
The app should either bundle ClickMonitorDDC or check for it on startup and prompt Ben to install it if missing.

### Colour temperature — f.lux

f.lux adjusts GPU colour output via its own API / command line. It must already be installed — it's not something the app installs.

f.lux CLI options:

```
# f.lux doesn't have a robust CLI, so control via its config file or registry keys
# Alternative: use Windows built-in Night Light via PowerShell as fallback
```

**Note:** f.lux's fullscreen game exception should be surfaced as a toggle in the Game profile settings. This tells f.lux to automatically disengage when a fullscreen app is running.

Known issue: f.lux colour transitions can cause brief flicker with G-Sync. Setting transition speed to "slow" in f.lux mitigates this — mention this to Ben in the app's first-run notes.

### Optional — Logitech G-Hub profile switching

Ben runs G910 keyboard, G903 mouse, and G733 headset — all Logitech, all managed by G-Hub. G-Hub supports profile switching per application. If feasible, the app could trigger a G-Hub profile switch when changing display modes (e.g. different keyboard lighting for each mode). This is a nice-to-have, not a requirement.

---

## App requirements

### Must have

- System tray icon — minimal footprint, always accessible
- Three named profiles (Work, Code, Game) switchable from tray menu
- Per-profile customisation: brightness %, colour temperature, f.lux on/off
- Configurable hotkeys per profile (suggested defaults: Win+1, Win+2, Win+3)
- Auto-switch by time of day (e.g. Work at 8am, Code at 6pm) — configurable or disable-able
- Settings UI — clean, modern, not a throwback to 2003
- Persistent config saved to disk (JSON is fine)
- Graceful handling if ClickMonitorDDC or f.lux isn't found — warn Ben, don't crash

### Nice to have

- Transition speed setting (instant vs gradual)
- Break reminder toggle per profile (on for Work, off for Game)
- Tray tooltip showing active profile
- G-Hub profile switching (if feasible without major complexity)
- A "current settings" display showing actual brightness and colour temp

### Don't bother

- Cloud sync
- Analytics
- Anything requiring admin elevation to run normally

---

## Tech stack recommendation

**Python + customtkinter** for the UI — modern looking, good tray support via `pystray`, packages cleanly to a standalone `.exe` via PyInstaller so Ben doesn't need Python installed.

Key libraries:

- `customtkinter` — modern UI
- `pystray` — system tray
- `pillow` — tray icon image handling
- `keyboard` — global hotkeys
- `schedule` — time-based auto-switching
- `pyinstaller` — packaging to .exe

If you have a strong reason to use a different stack, go for it — but explain the choice to Ben before diving in.

---

## File location

Ben works off his **E: drive**. Put the project there, e.g.:

```
E:\Projects\DisplayManager\
```

---

## Coding philosophy — Ben's preference

Ben has a strong engineering preference for **building holistically from the start rather than retrofitting**. Don't build a skeleton and say "we'll add that later." Think through the architecture properly first, then build it right.

He also has a dry sense of humour about over-engineering — don't build a spaceship when a ute will do. Keep it appropriately scoped.

---

## First steps

1. Verify ClickMonitorDDC can communicate with the PG349Q via DDC/CI — run a test brightness command and confirm it works before building the UI around it
2. Check how f.lux exposes control (config file, registry, API) — this affects how the Code and Game profiles work
3. Set up the project structure on E:\Projects\DisplayManager\
4. Build the core profile switching logic before the UI
5. UI last — functionality first

---

## Questions to ask Ben if anything is unclear

- What brightness levels feel right to him for each profile? (start with the defaults above, let him adjust)
- Does he want the app to start with Windows automatically?
- Does he want a first-run setup wizard or just sensible defaults he can tweak?

---

_Document written by Claude (claude.ai) — April 2026_
_Refer back to this brief if scope creep appears. Ben's goal is a clean, functional tray app — not a platform._
