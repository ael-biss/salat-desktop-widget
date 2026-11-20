"""Always-on-top draggable desktop pill widget and main controller."""

import datetime
from typing import Dict, List, Optional, Set

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

from salat_widget.constants import APP_NAME
from salat_widget.core.calculator import find_active_prayer, format_countdown, parse_prayer_entries
from salat_widget.models import ActivePrayer, PrayerEntry, UserConfig
from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.services.system_service import SystemService
from salat_widget.ui.popup_window import PopupWindow
from salat_widget.ui.settings_window import SettingsWindow
from salat_widget.ui.styles import enable_rgba, load_mosque_icon


class PillWindow(Gtk.Window):
    def __init__(
        self,
        config_service: ConfigService,
        prayer_service: PrayerService,
        audio_service: AudioService,
        system_service: SystemService,
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config_service = config_service
        self.prayer_service = prayer_service
        self.audio_service = audio_service
        self.system_service = system_service

        self.day_data: Optional[Dict[str, str]] = None
        self.entries: List[PrayerEntry] = []
        self.active: Optional[ActivePrayer] = None
        self.last_fetch_date: Optional[datetime.date] = None
        self.triggered_events: Set[str] = set()

        self._dragging = False
        self._drag_moved = False
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self._win_start_x = 0
        self._win_start_y = 0

        self.get_style_context().add_class('salat-transparent')
        self.set_title(APP_NAME)
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_accept_focus(False)
        self.set_resizable(False)
        self.stick()
        enable_rgba(self)

        event_box = Gtk.EventBox()
        event_box.set_visible_window(False)
        event_box.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
        )
        event_box.connect('button-press-event', self._on_button_press)
        event_box.connect('button-release-event', self._on_button_release)
        event_box.connect('motion-notify-event', self._on_motion)

        self.pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.pill.get_style_context().add_class('salat-pill')
        event_box.add(self.pill)
        self.add(event_box)

        pixbuf = load_mosque_icon(16)
        if pixbuf:
            self.pill.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)

        self.name_lbl = Gtk.Label(label='Salat')
        self.name_lbl.get_style_context().add_class('salat-pill-name')
        self.pill.pack_start(self.name_lbl, False, False, 0)

        sep_lbl = Gtk.Label(label='|')
        sep_lbl.get_style_context().add_class('salat-pill-sep')
        self.pill.pack_start(sep_lbl, False, False, 0)

        self.time_lbl = Gtk.Label(label='--:--')
        self.time_lbl.get_style_context().add_class('salat-pill-time')
        self.pill.pack_start(self.time_lbl, False, False, 0)

        self.settings_win = SettingsWindow(
            config_service=self.config_service,
            audio_service=self.audio_service,
            on_reset_position=self.reset_position,
            on_refresh_schedule=lambda: self.refresh_data(force=True),
        )
        self.popup_win = PopupWindow(
            config_service=self.config_service,
            on_open_settings=self.settings_win.open_window,
            on_refresh=lambda: self.refresh_data(force=True),
        )

        self.config_service.subscribe(self._on_config_changed)

        self.show_all()
        GLib.idle_add(self._apply_initial_position)

        self.refresh_data(force=False)
        GLib.timeout_add_seconds(1, self._on_tick)

    def _on_config_changed(self, _cfg: UserConfig) -> None:
        self._on_tick()
        if self.popup_win.get_visible():
            self.popup_win.update_content(self.day_data, self.active, self.entries, datetime.datetime.now())

    def _apply_initial_position(self) -> bool:
        cfg = self.config_service.config
        if isinstance(cfg.widget_x, int) and isinstance(cfg.widget_y, int):
            self.move(cfg.widget_x, cfg.widget_y)
        else:
            self.reset_position()
        return False

    def reset_position(self) -> None:
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        width, _ = self.get_size()
        x = geo.x + geo.width - max(width, 160) - 16
        y = geo.y + 38
        self.move(x, y)
        self.config_service.config.widget_x = x
        self.config_service.config.widget_y = y
        self.config_service.save(notify=False)

    def _on_button_press(self, _widget, event) -> bool:
        if event.button == 1:
            self._dragging = True
            self._drag_moved = False
            self._drag_start_x = event.x_root
            self._drag_start_y = event.y_root
            self._win_start_x, self._win_start_y = self.get_position()
            return True
        if event.button == 3:
            self.popup_win.hide()
            self.settings_win.open_window()
            return True
        return False

    def _on_motion(self, _widget, event) -> bool:
        if not self._dragging:
            return False
        dx = int(event.x_root - self._drag_start_x)
        dy = int(event.y_root - self._drag_start_y)
        if abs(dx) > 4 or abs(dy) > 4:
            self._drag_moved = True
            if self.popup_win.get_visible():
                self.popup_win.hide()
            self.move(self._win_start_x + dx, self._win_start_y + dy)
        return True

    def _on_button_release(self, _widget, event) -> bool:
        if event.button == 1 and self._dragging:
            self._dragging = False
            if self._drag_moved:
                x, y = self.get_position()
                self.config_service.config.widget_x = x
                self.config_service.config.widget_y = y
                self.config_service.save(notify=False)
            else:
                self.popup_win.toggle_near(self, self.day_data, self.active, self.entries)
            return True
        return False

    def refresh_data(self, force: bool = False) -> None:
        today = datetime.date.today()
        if not self.day_data:
            self.name_lbl.set_text('Sync...')

        def handle_success(data: Dict[str, str]) -> None:
            GLib.idle_add(self._on_data_loaded, data, today)

        def handle_error(_msg: str) -> None:
            GLib.idle_add(self._on_data_error)

        self.prayer_service.fetch_async(
            today=today,
            force=force,
            on_success=handle_success,
            on_error=handle_error,
        )

    def _on_data_loaded(self, data: Dict[str, str], today: datetime.date) -> bool:
        self.day_data = data
        self.last_fetch_date = today
        self._on_tick()
        if self.popup_win.get_visible():
            self.popup_win.update_content(self.day_data, self.active, self.entries, datetime.datetime.now())
        return False

    def _on_data_error(self) -> bool:
        if not self.day_data:
            self.name_lbl.set_text('Offline')
            self.time_lbl.set_text('--:--')
        return False

    def _on_tick(self) -> bool:
        now = datetime.datetime.now()
        today = now.date()

        if self.last_fetch_date and self.last_fetch_date != today:
            self.triggered_events.clear()
            self.refresh_data(force=False)

        if not self.day_data:
            return True

        cfg = self.config_service.config
        self.entries = parse_prayer_entries(self.day_data, cfg.iqama_delays, now)
        self.active = find_active_prayer(self.entries, cfg.iqama_delays, now)
        if not self.active:
            return True

        phase = self.active.phase
        prayer = self.active.prayer
        ctx = self.pill.get_style_context()

        if phase == 'IQAMA':
            ctx.add_class('iqama-mode')
            diff = (prayer.iqama_dt - now).total_seconds()
            self.name_lbl.set_text(f'Iqama {prayer.name}')
            self.time_lbl.set_text(format_countdown(diff))

            adhan_key = f'{today.isoformat()}-adhan-{prayer.key}'
            if adhan_key not in self.triggered_events and (now - prayer.adhan_dt).total_seconds() < 15:
                self.triggered_events.add(adhan_key)
                self.system_service.notify(
                    f'{prayer.name} Adhan',
                    f'It is time for {prayer.name} prayer in Sala Al Jadida.',
                    enabled=cfg.notifications_enabled,
                )
                if cfg.audio_enabled:
                    self.audio_service.play(cfg.adhan_audio_path)

            if diff <= 1:
                iqama_key = f'{today.isoformat()}-iqama-{prayer.key}'
                if iqama_key not in self.triggered_events:
                    self.triggered_events.add(iqama_key)
                    self.system_service.notify(
                        f'{prayer.name} Iqama',
                        'Congregation prayer is starting now.',
                        enabled=cfg.notifications_enabled,
                    )
                    self.system_service.lock_screen(
                        command=cfg.custom_lock_command,
                        enabled=cfg.lock_enabled,
                    )
        else:
            ctx.remove_class('iqama-mode')
            diff = (prayer.adhan_dt - now).total_seconds()
            self.name_lbl.set_text(prayer.name)
            self.time_lbl.set_text(format_countdown(diff))

        if self.popup_win.get_visible():
            self.popup_win.update_hero(self.active, self.entries, now)

        return True
