#!/usr/bin/env python3
"""Entrypoint for the Sala Al Jadida Salat Desktop Widget."""

import signal

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.services.system_service import SystemService
from salat_widget.ui.pill_window import PillWindow
from salat_widget.ui.styles import install_css


def main() -> None:
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    install_css()

    config_service = ConfigService()
    prayer_service = PrayerService()
    audio_service = AudioService()
    system_service = SystemService()

    PillWindow(
        config_service=config_service,
        prayer_service=prayer_service,
        audio_service=audio_service,
        system_service=system_service,
    )
    Gtk.main()


if __name__ == '__main__':
    main()
