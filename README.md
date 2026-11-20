# Salat Desktop Widget (Sala Al Jadida)

A clean, modular, standalone always-on-top desktop widget for **Sala Al Jadida** prayer times and Iqama countdowns.  
Runs completely in user space — **no `sudo` and no GNOME Shell extension required**.

## Architecture

```text
salat-desktop-widget/
├── run.py                      # Application entrypoint & dependency wiring
├── Makefile                    # Run, stop, autostart, and syntax check targets
├── assets/
│   ├── adan.mp3                # Default Adhan audio
│   └── mosque.svg              # Vector icon used in pill, popup, and settings
└── salat_widget/
    ├── constants.py            # Paths, Sala Al Jadida API URL, defaults
    ├── models.py               # Typed dataclasses (UserConfig, PrayerEntry, ActivePrayer)
    ├── core/
    │   └── calculator.py       # Pure prayer countdown & progress calculations
    ├── services/
    │   ├── config_service.py   # Config persistence (~/.config/salat-widget/config.json) + observers
    │   ├── prayer_service.py   # Async monthly schedule fetch & local caching
    │   ├── audio_service.py    # In-process GStreamer Adhan playback + test/stop
    │   └── system_service.py   # Desktop notifications & Auto-Lock (ft_lock / custom cmd)
    └── ui/
        ├── styles.py           # Centralized dark slate + emerald GTK3 theme
        ├── pill_window.py      # Draggable always-on-top floating pill & tick controller
        ├── popup_window.py     # Schedule popup with hero countdown & daily prayer table
        └── settings_window.py  # Dedicated Settings window (Iqama times, audio, alerts, lock)
```

## Features
- **Always-on-top floating pill** pinned across all workspaces (hidden from taskbar/Alt-Tab).
- **Draggable** anywhere on screen with saved coordinates.
- **Schedule popup** (left-click pill): Hero countdown, progress bar, and all daily prayer times with Iqama badges.
- **Full Settings window** (click **Settings** in popup or right-click the pill):
  - Customize **Iqama delay** per prayer (Fajr, Dhuhr, Asr, Maghrib, Isha) with live updates.
  - Toggle **Desktop Notifications** and **Adhan Audio**, pick a custom audio file, and test/stop playback.
  - Toggle **Auto-Lock on Iqama** and customize the lock command (default: `ft_lock`).
  - Refresh schedule or reset pill position.

## Usage

```bash
# Start (or restart) the widget
make run

# Enable auto-start on login
make autostart

# Stop the widget
make stop
```
