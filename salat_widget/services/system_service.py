"""Desktop notifications and screen-lock execution service."""

import subprocess

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify

from salat_widget.constants import APP_NAME


class SystemService:
    def __init__(self) -> None:
        Notify.init(APP_NAME)

    def notify(self, title: str, body: str, enabled: bool = True) -> None:
        if not enabled:
            return
        try:
            notification = Notify.Notification.new(title, body, 'appointment-soon')
            notification.show()
        except Exception:
            pass

    def lock_screen(self, command: str = 'ft_lock', enabled: bool = False) -> None:
        if not enabled:
            return
        cmd = (command or '').strip() or 'ft_lock'
        try:
            subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception:
            pass
