"""Asynchronous GStreamer audio playback service."""

import os
from typing import Optional

import gi
gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst

from salat_widget.constants import DEFAULT_ADHAN_PATH


class AudioService:
    def __init__(self) -> None:
        Gst.init(None)
        self._player = None

    def resolve_path(self, custom_path: str) -> Optional[str]:
        candidate = (custom_path or '').strip()
        if candidate:
            expanded = os.path.abspath(os.path.expanduser(candidate))
            if os.path.exists(expanded):
                return expanded
        if os.path.exists(DEFAULT_ADHAN_PATH):
            return DEFAULT_ADHAN_PATH
        return None

    def play(self, custom_path: str = '') -> bool:
        path = self.resolve_path(custom_path)
        if not path:
            return False

        self.stop()
        player = Gst.ElementFactory.make('playbin', 'salat_adhan_player')
        if not player:
            return False

        uri = GLib.filename_to_uri(path, None)
        player.set_property('uri', uri)

        bus = player.get_bus()
        bus.add_signal_watch()
        bus.connect('message::eos', lambda *_: self.stop())
        bus.connect('message::error', lambda *_: self.stop())

        ret = player.set_state(Gst.State.PLAYING)
        if ret == Gst.StateChangeReturn.FAILURE:
            player.set_state(Gst.State.NULL)
            return False

        self._player = player
        return True

    def stop(self) -> None:
        if self._player is not None:
            try:
                self._player.set_state(Gst.State.NULL)
            except Exception:
                pass
            self._player = None

    @property
    def is_playing(self) -> bool:
        return self._player is not None
