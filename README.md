# Salat Desktop Widget (Sala Al Jadida)

A clean, modular, standalone always-on-top desktop widget for **Sala Al Jadida** prayer times, Iqama countdowns, and Jumu'ah reminders.  
Runs completely in user space — **no `sudo`, no GNOME Shell extension, and no source code required for end users**.

## 1-Line Install (End Users)

```bash
curl -fsSL https://raw.githubusercontent.com/ael-biss/salat-desktop-widget/main/install.sh | bash
```

This downloads the compiled single-file bundle to `~/.local/bin/salat-widget`, enables login autostart in `~/.config/autostart/salat-desktop-widget.desktop`, and launches the widget.

## Features
- **Always-on-top floating pill**: Pinned across all workspaces (hidden from taskbar/Alt-Tab), defaults to top-left, draggable anywhere.
- **Red Iqama Alert Mode**: Switches the minaret icon and pill/hero theme from green to red during the Iqama countdown.
- **Full Monthly Schedule**: View the entire Hijri/Gregorian month table from the popup.
- **Jumu'ah (Friday) Reminder**: Configurable reminder notification before Friday prayer, plus `Jumu'ah` label on Fridays.
- **Full Settings Window** (explicit **Save / Cancel**):
  - Customize Iqama delays per prayer (Fajr, Dhuhr, Asr, Maghrib, Isha).
  - Toggle Desktop Notifications, Jumu'ah Reminder, Adhan Audio (with custom file picker + Test/Stop), and Auto-Lock (`ft_lock` or custom command).
  - Built-in **Check for Updates / Install** powered by GitHub Releases.

## Developer Commands

```bash
make test       # Run automated unit tests
make build      # Build bytecode-only dist/salat-widget.pyz (0 .py source files)
make install    # Build & install locally to ~/.local/bin/salat-widget + autostart
make uninstall  # Remove installed app, assets, and autostart
make run        # Run directly from source
make stop       # Stop running widget
make sim-adhan  # Simulate Adhan -> Red Iqama transition
make sim-iqama  # Simulate Red Iqama countdown
make sim-jumaa  # Simulate Friday Jumu'ah reminder
```

## Publishing Updates to All Users

1. Bump `__version__` in `salat_widget/__init__.py`.
2. Commit and push a version tag:
   ```bash
   git tag v1.0.1
   git push origin main --tags
   ```
3. GitHub Actions automatically builds `salat-widget.pyz` and publishes the release. All installed users are notified and can update in one click from **Settings → Check for Updates → Install**.

And whenever you want to push an update to all users in the future, just bump `__version__` in `salat_widget/__init__.py`, commit, and push a new tag (e.g., `git tag v1.0.1 && git push origin main --tags`).
