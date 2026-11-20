#!/usr/bin/env python3
"""Entrypoint for the Sala Al Jadida Salat Desktop Widget."""

import argparse
import signal
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib, Gtk

from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.services.system_service import SystemService
from salat_widget.ui.pill_window import PillWindow
from salat_widget.ui.styles import install_css


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Sala Al Jadida Salat Desktop Widget')
    parser.add_argument(
        '--simulate',
        choices=['adhan', 'iqama', 'jumaa'],
        default=None,
        help='Run a live visual/audio simulation for adhan, iqama (red icon), or jumaa reminder',
    )
    return parser.parse_args()


class SalatApp:
    def __init__(self, simulate: Optional[str] = None) -> None:
        self.simulate = simulate
        self.config_service = ConfigService()
        self.prayer_service = PrayerService()
        self.audio_service = AudioService()
        self.system_service = SystemService()
        self.pill: Optional[PillWindow] = None
        self._spawn_pill(open_settings=False)

    def _spawn_pill(self, open_settings: bool) -> None:
        self.pill = PillWindow(
            config_service=self.config_service,
            prayer_service=self.prayer_service,
            audio_service=self.audio_service,
            system_service=self.system_service,
            simulate=self.simulate,
            on_overlay_changed=self._on_overlay_changed,
        )
        if open_settings:
            GLib.idle_add(self.pill.settings_win.open_window)

    def _on_overlay_changed(self, _enabled: bool) -> None:
        old = self.pill
        if old is not None:
            old.cleanup()
        self._spawn_pill(open_settings=False)


def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    install_css()

    SalatApp(simulate=args.simulate)
    Gtk.main()


if __name__ == '__main__':
    main()
