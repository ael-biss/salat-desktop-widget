#!/usr/bin/env python3
"""Entrypoint for the Sala Al Jadida Salat Desktop Widget."""

import argparse
import signal
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.services.system_service import SystemService
from salat_widget.services.update_service import UpdateService
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


class AppController:
    def __init__(self, simulate: Optional[str] = None) -> None:
        self.simulate = simulate
        self.config_service = ConfigService()
        self.prayer_service = PrayerService()
        self.audio_service = AudioService()
        self.system_service = SystemService()
        self.update_service = UpdateService()
        self.pill: Optional[PillWindow] = None
        self._create_pill(check_updates=True)

    def _create_pill(
        self,
        initial_day_data=None,
        initial_triggered_events=None,
        check_updates: bool = False,
    ) -> None:
        self.pill = PillWindow(
            config_service=self.config_service,
            prayer_service=self.prayer_service,
            audio_service=self.audio_service,
            system_service=self.system_service,
            update_service=self.update_service,
            simulate=self.simulate,
            on_top_bar_mode_changed=self._on_mode_changed,
            initial_day_data=initial_day_data,
            initial_triggered_events=initial_triggered_events,
            check_updates=check_updates,
        )

    def _on_mode_changed(self, _top_bar_enabled: bool) -> bool:
        day_data = None
        triggered = None
        if self.pill is not None:
            day_data = self.pill.day_data
            triggered = set(self.pill.triggered_events)
            self.pill.cleanup()
            self.pill = None
        self._create_pill(
            initial_day_data=day_data,
            initial_triggered_events=triggered,
            check_updates=False,
        )
        return False


def main() -> None:
    args = parse_args()
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    install_css()
    controller = AppController(simulate=args.simulate)
    try:
        Gtk.main()
    finally:
        if controller.pill is not None:
            controller.pill.cleanup()


if __name__ == '__main__':
    main()
