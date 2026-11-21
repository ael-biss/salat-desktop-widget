"""Always-on-top draggable desktop pill widget and GNOME Top Bar overlay controller."""

import datetime
import os
import sys
from typing import Callable, Dict, List, Optional, Set, Tuple

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

from salat_widget.constants import APP_NAME
from salat_widget.core.calculator import (
    check_jumaa_reminder,
    find_active_prayer,
    format_countdown,
    parse_prayer_entries,
)
from salat_widget.i18n import is_rtl, prayer_name, tr
from salat_widget.models import ActivePrayer, PrayerEntry, UserConfig
from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.services.system_service import SystemService
from salat_widget.services.update_service import UpdateService
from salat_widget.services.x11_topbar import (
    BUTTON1_MASK,
    BUTTON2_MASK,
    X11TopBarInputMonitor,
    is_x11_session,
)
from salat_widget.ui.popup_window import PopupWindow
from salat_widget.ui.schedule_window import ScheduleWindow
from salat_widget.ui.settings_window import SettingsWindow
from salat_widget.ui.styles import apply_rtl_layout, enable_rgba, load_mosque_icon


class PillWindow(Gtk.Window):
    def __init__(
        self,
        config_service: ConfigService,
        prayer_service: PrayerService,
        audio_service: AudioService,
        system_service: SystemService,
        update_service: Optional[UpdateService] = None,
        simulate: Optional[str] = None,
        on_top_bar_mode_changed: Optional[Callable[[bool], None]] = None,
        initial_day_data: Optional[Dict[str, str]] = None,
        initial_triggered_events: Optional[Set[str]] = None,
        check_updates: bool = True,
    ) -> None:
        self._top_bar_mode = bool(config_service.config.top_bar_mode) and is_x11_session()
        win_type = Gtk.WindowType.POPUP if self._top_bar_mode else Gtk.WindowType.TOPLEVEL
        super().__init__(type=win_type)

        self.config_service = config_service
        self.prayer_service = prayer_service
        self.audio_service = audio_service
        self.system_service = system_service
        self.update_service = update_service or UpdateService()
        self.simulate = simulate
        self.on_top_bar_mode_changed = on_top_bar_mode_changed
        self._sim_start = datetime.datetime.now()
        self._tick_source_id: Optional[int] = None
        self._x11_monitor: Optional[X11TopBarInputMonitor] = None
        self._hidden_by_env = False

        self.day_data: Optional[Dict[str, str]] = initial_day_data
        self.entries: List[PrayerEntry] = []
        self.active: Optional[ActivePrayer] = None
        self.last_fetch_date: Optional[datetime.date] = datetime.date.today() if initial_day_data else None
        self.triggered_events: Set[str] = set(initial_triggered_events) if initial_triggered_events else set()

        self._pos_x: int = 0
        self._pos_y: int = 0

        # Floating-mode GTK drag state
        self._dragging = False
        self._drag_moved = False
        self._drag_start_x = 0.0
        self._drag_start_y = 0.0
        self._win_start_x = 0
        self._win_start_y = 0

        # Top-bar XInput2 raw interaction state
        self._raw_dragging = False
        self._raw_drag_button = 0
        self._raw_drag_moved = False
        self._raw_drag_start_x = 0
        self._raw_drag_start_y = 0
        self._raw_win_start_x = 0
        self._raw_hovered = False

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
        if not self._top_bar_mode:
            event_box.add_events(
                Gdk.EventMask.BUTTON_PRESS_MASK
                | Gdk.EventMask.BUTTON_RELEASE_MASK
                | Gdk.EventMask.POINTER_MOTION_MASK
            )
            event_box.connect('button-press-event', self._on_button_press)
            event_box.connect('button-release-event', self._on_button_release)
            event_box.connect('motion-notify-event', self._on_motion)

        spacing = 6 if self._top_bar_mode else 8
        self.pill = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=spacing)
        self.pill.get_style_context().add_class('salat-pill')
        if self._top_bar_mode:
            self.pill.get_style_context().add_class('top-bar-mode')
        event_box.add(self.pill)
        self.add(event_box)

        icon_size = 14 if self._top_bar_mode else 16
        self._icon_green = load_mosque_icon(icon_size, red=False)
        self._icon_red = load_mosque_icon(icon_size, red=True)
        self._is_red_icon = False
        self.icon_widget = Gtk.Image()
        if self._icon_green:
            self.icon_widget.set_from_pixbuf(self._icon_green)
            self.pill.pack_start(self.icon_widget, False, False, 0)

        self.name_lbl = Gtk.Label(label=tr(self.config_service.config.language, 'salat'))
        self.name_lbl.get_style_context().add_class('salat-pill-name')
        self.pill.pack_start(self.name_lbl, False, False, 0)

        sep_lbl = Gtk.Label(label='|')
        sep_lbl.get_style_context().add_class('salat-pill-sep')
        self.pill.pack_start(sep_lbl, False, False, 0)

        self.time_lbl = Gtk.Label(label='--:--')
        self.time_lbl.set_direction(Gtk.TextDirection.LTR)
        self.time_lbl.get_style_context().add_class('salat-pill-time')
        self.pill.pack_start(self.time_lbl, False, False, 0)

        self.settings_win = SettingsWindow(
            config_service=self.config_service,
            audio_service=self.audio_service,
            update_service=self.update_service,
            on_reset_position=self.reset_position,
            on_refresh_schedule=lambda: self.refresh_data(force=True),
            on_top_bar_mode_changed=self._handle_top_bar_mode_changed,
            on_top_bar_preset=self.apply_top_bar_preset,
            on_reload_app=self.reload_app,
            on_quit_app=self.quit_app,
        )
        self.schedule_win = ScheduleWindow(
            prayer_service=self.prayer_service,
            config_service=self.config_service,
        )
        self.popup_win = PopupWindow(
            config_service=self.config_service,
            on_open_settings=self.settings_win.open_window,
            on_open_schedule=self.schedule_win.open_window,
            on_refresh=lambda: self.refresh_data(force=True),
            on_reload=self.reload_app,
            on_quit=self.quit_app,
        )

        self.connect('size-allocate', self._on_size_allocate)
        self.config_service.subscribe(self._on_config_changed)

        if self._top_bar_mode:
            self._x11_monitor = X11TopBarInputMonitor(
                on_button_press=self._on_raw_button_press,
                on_button_release=self._on_raw_button_release,
                on_motion=self._on_raw_motion,
                on_screensaver_changed=self._on_screensaver_changed,
            )
            if not self._x11_monitor.start():
                self._x11_monitor = None
                self.config_service.config.top_bar_mode = False
                self.config_service.save(notify=False)
                if self.on_top_bar_mode_changed:
                    GLib.idle_add(self.on_top_bar_mode_changed, False)

        self.show_all()
        apply_rtl_layout(self, is_rtl(self.config_service.config.language), ltr_widgets=(self.time_lbl,))
        GLib.idle_add(self._apply_initial_position)

        if self.day_data:
            self._on_tick()
        else:
            self.refresh_data(force=False)
        self._tick_source_id = GLib.timeout_add_seconds(1, self._on_tick)

        if check_updates and self.update_service.is_configured and not self.simulate:
            self.update_service.check_async(self._on_startup_update_check)

    def cleanup(self) -> None:
        if self._tick_source_id is not None:
            GLib.source_remove(self._tick_source_id)
            self._tick_source_id = None
        if self._x11_monitor is not None:
            self._x11_monitor.stop()
            self._x11_monitor = None
        self.config_service.unsubscribe(self._on_config_changed)
        self.popup_win.destroy()
        self.schedule_win.destroy()
        self.settings_win.destroy()
        self.destroy()

    def _handle_top_bar_mode_changed(self, enabled: bool) -> bool:
        if self.on_top_bar_mode_changed:
            self.on_top_bar_mode_changed(enabled)
        return False

    def reload_app(self) -> None:
        self.audio_service.stop()
        if self._x11_monitor is not None:
            self._x11_monitor.stop()
            self._x11_monitor = None
        os.execv(sys.executable, [sys.executable] + sys.argv)

    def quit_app(self) -> None:
        self.audio_service.stop()
        Gtk.main_quit()

    def _on_startup_update_check(
        self,
        remote_version: Optional[str],
        _download_url: Optional[str],
        _error: Optional[str],
    ) -> None:
        if remote_version:
            lang = self.config_service.config.language
            GLib.idle_add(
                self.system_service.notify,
                tr(lang, 'notif_update_title'),
                tr(lang, 'notif_update_body', version=remote_version),
                self.config_service.config.notifications_enabled,
            )

    def _on_config_changed(self, cfg: UserConfig) -> None:
        apply_rtl_layout(self, is_rtl(cfg.language), ltr_widgets=(self.time_lbl,))
        self.popup_win.apply_language(cfg.language)
        self.schedule_win.apply_language(cfg.language)
        self._on_tick()
        if self.popup_win.get_visible():
            self.popup_win.update_content(self.day_data, self.active, self.entries, datetime.datetime.now())

    def _get_monitor_metrics(self) -> Tuple[Gdk.Rectangle, int]:
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        wa = monitor.get_workarea()
        raw_panel_h = wa.y - geo.y
        panel_h = raw_panel_h if 16 <= raw_panel_h <= 64 else 28
        return (geo, panel_h)

    def _top_bar_y(self) -> int:
        geo, panel_h = self._get_monitor_metrics()
        _, height = self.get_size()
        return geo.y + max(0, (panel_h - height) // 2)

    def _move_to(self, x: int, y: int) -> None:
        self._pos_x = x
        self._pos_y = y
        self.move(x, y)

    def get_screen_rect(self) -> Tuple[int, int, int, int]:
        width, height = self.get_size()
        if self._top_bar_mode:
            return (self._pos_x, self._pos_y, width, height)
        px, py = self.get_position()
        return (px, py, width, height)

    def _clamp_position(self, x: int, y: int) -> Tuple[int, int]:
        geo, panel_h = self._get_monitor_metrics()
        width, height = self.get_size()
        min_x = geo.x + 4
        max_x = geo.x + geo.width - max(width, 120) - 4
        if self._top_bar_mode:
            return (max(min_x, min(x, max_x)), self._top_bar_y())
        # Keep floating pill below GNOME Shell's top bar so clicks are never intercepted
        min_y = geo.y + panel_h
        max_y = geo.y + geo.height - max(height, 30) - 4
        return (max(min_x, min(x, max_x)), max(min_y, min(y, max_y)))

    def _on_size_allocate(self, _widget, _allocation) -> None:
        if not self._top_bar_mode or self._hidden_by_env:
            return
        nx, ny = self._clamp_position(self._pos_x, self._top_bar_y())
        if nx != self._pos_x or ny != self._pos_y:
            self._move_to(nx, ny)

    def _apply_initial_position(self) -> bool:
        cfg = self.config_service.config
        if self._top_bar_mode:
            if isinstance(cfg.top_bar_x, int):
                cx, cy = self._clamp_position(cfg.top_bar_x, self._top_bar_y())
                self._move_to(cx, cy)
                if cx != cfg.top_bar_x:
                    cfg.top_bar_x = cx
                    self.config_service.save(notify=False)
            else:
                self.reset_position()
            self._update_env_visibility()
            return False

        if isinstance(cfg.widget_x, int) and isinstance(cfg.widget_y, int):
            cx, cy = self._clamp_position(cfg.widget_x, cfg.widget_y)
            self._move_to(cx, cy)
            if cx != cfg.widget_x or cy != cfg.widget_y:
                cfg.widget_x, cfg.widget_y = cx, cy
                self.config_service.save(notify=False)
        else:
            self.reset_position()
        return False

    def apply_top_bar_preset(self, preset: str) -> None:
        geo, _ = self._get_monitor_metrics()
        width, _ = self.get_size()
        if preset == 'left':
            target_x = geo.x + int(geo.width * 0.28)
        elif preset == 'far_right':
            target_x = geo.x + geo.width - max(width, 150) - 210
        else:
            # Default 'right': clean empty space between GNOME center clock and right tray
            target_x = geo.x + int(geo.width * 0.62)

        if self._top_bar_mode:
            nx, ny = self._clamp_position(target_x, self._top_bar_y())
            self._move_to(nx, ny)
            self.config_service.config.top_bar_x = nx
        else:
            self.config_service.config.top_bar_x = target_x
        self.config_service.save(notify=False)

    def reset_position(self) -> None:
        if self._top_bar_mode:
            self.apply_top_bar_preset('right')
            return
        geo, panel_h = self._get_monitor_metrics()
        x = geo.x + 12
        y = geo.y + panel_h + 4
        x, y = self._clamp_position(x, y)
        self._move_to(x, y)
        self.config_service.config.widget_x = x
        self.config_service.config.widget_y = y
        self.config_service.save(notify=False)

    # --- Top Bar Mode XInput2 Raw Pointer Handlers ---

    def _x11_to_logical(self, rx_px: int, ry_px: int) -> Tuple[int, int]:
        scale = max(1, self.get_scale_factor())
        return (rx_px // scale, ry_px // scale)

    def _hit_test_top_bar(self, lx: int, ly: int) -> bool:
        if self._hidden_by_env or not self.get_visible():
            return False
        geo, panel_h = self._get_monitor_metrics()
        px, py, pw, ph = self.get_screen_rect()
        top_edge = min(py, geo.y)
        bottom_edge = max(py + ph, geo.y + panel_h)
        return (px <= lx <= px + pw) and (top_edge <= ly <= bottom_edge)

    def _set_raw_hover(self, hovered: bool) -> None:
        if hovered == self._raw_hovered:
            return
        self._raw_hovered = hovered
        ctx = self.pill.get_style_context()
        if hovered:
            ctx.add_class('salat-pill-hover')
        else:
            ctx.remove_class('salat-pill-hover')

    def _on_raw_button_press(self, button: int, rx_px: int, ry_px: int) -> None:
        lx, ly = self._x11_to_logical(rx_px, ry_px)
        if not self._hit_test_top_bar(lx, ly):
            return
        if button in (1, 2):
            self._raw_dragging = True
            self._raw_drag_button = button
            self._raw_drag_moved = False
            self._raw_drag_start_x = lx
            self._raw_drag_start_y = ly
            self._raw_win_start_x = self._pos_x
        elif button == 3:
            self.popup_win.hide()
            self.settings_win.open_window()

    def _finish_raw_drag(self, button: int) -> None:
        was_moved = self._raw_drag_moved
        self._raw_dragging = False
        self._raw_drag_button = 0
        self._raw_drag_moved = False
        if was_moved:
            self.config_service.config.top_bar_x = self._pos_x
            self.config_service.save(notify=False)
        elif button == 1:
            self.popup_win.toggle_near(self, self.day_data, self.active, self.entries)

    def _on_raw_motion(self, rx_px: int, ry_px: int, mask: int) -> None:
        lx, ly = self._x11_to_logical(rx_px, ry_px)
        self._set_raw_hover(self._hit_test_top_bar(lx, ly))
        if not self._raw_dragging:
            return
        # Failsafe: verify physical button is still held (prevents stuck drag even if a release event is dropped)
        expected_mask = BUTTON1_MASK if self._raw_drag_button == 1 else BUTTON2_MASK
        if (mask & expected_mask) == 0:
            self._finish_raw_drag(self._raw_drag_button)
            return
        dx = lx - self._raw_drag_start_x
        if abs(dx) > 6:
            self._raw_drag_moved = True
            if self.popup_win.get_visible():
                self.popup_win.hide()
            nx, ny = self._clamp_position(self._raw_win_start_x + dx, self._top_bar_y())
            self._move_to(nx, ny)

    def _on_raw_button_release(self, button: int, _rx_px: int, _ry_px: int) -> None:
        if not self._raw_dragging or button != self._raw_drag_button:
            return
        self._finish_raw_drag(button)

    def _on_screensaver_changed(self, _active: bool) -> None:
        GLib.idle_add(self._update_env_visibility)

    def _update_env_visibility(self) -> bool:
        if not self._top_bar_mode or not self._x11_monitor:
            return False
        should_hide = (
            self._x11_monitor.screensaver_active
            or self._x11_monitor.is_fullscreen_active()
        )
        if should_hide and not self._hidden_by_env:
            self._hidden_by_env = True
            self._raw_dragging = False
            self._set_raw_hover(False)
            self.popup_win.hide()
            self.hide()
        elif not should_hide and self._hidden_by_env:
            self._hidden_by_env = False
            self.show_all()
            nx, ny = self._clamp_position(self._pos_x, self._top_bar_y())
            self._move_to(nx, ny)
        return False

    # --- Floating Mode GTK Pointer Handlers ---

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
            nx, ny = self._clamp_position(self._win_start_x + dx, self._win_start_y + dy)
            self._move_to(nx, ny)
        return True

    def _on_button_release(self, _widget, event) -> bool:
        if event.button == 1 and self._dragging:
            self._dragging = False
            if self._drag_moved:
                x, y = self.get_position()
                self._pos_x, self._pos_y = x, y
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
            self.name_lbl.set_text(tr(self.config_service.config.language, 'syncing'))

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
            self.name_lbl.set_text(tr(self.config_service.config.language, 'offline'))
            self.time_lbl.set_text('--:--')
        return False

    def _set_icon_red(self, is_red: bool) -> None:
        if is_red == self._is_red_icon:
            return
        self._is_red_icon = is_red
        pixbuf = self._icon_red if is_red else self._icon_green
        if pixbuf:
            self.icon_widget.set_from_pixbuf(pixbuf)

    def _build_simulated_state(self, now: datetime.datetime) -> Optional[tuple]:
        elapsed = (now - self._sim_start).total_seconds()
        lang = self.config_service.config.language
        if self.simulate == 'adhan':
            adhan_dt = self._sim_start + datetime.timedelta(seconds=3)
            iqama_dt = adhan_dt + datetime.timedelta(seconds=15)
            entry = PrayerEntry('Dhuhr', prayer_name('Dhuhr', lang), adhan_dt.strftime('%H:%M'), 1, adhan_dt, iqama_dt)
            phase = 'NEXT_ADHAN' if now < adhan_dt else ('IQAMA' if now < iqama_dt else 'NEXT_ADHAN')
            if now >= iqama_dt:
                entry = PrayerEntry('Asr', prayer_name('Asr', lang), (now + datetime.timedelta(hours=2)).strftime('%H:%M'), 12, now + datetime.timedelta(hours=2), now + datetime.timedelta(hours=2, minutes=12))
            return ([entry], ActivePrayer(phase=phase, prayer=entry), now)
        if self.simulate == 'iqama':
            adhan_dt = self._sim_start - datetime.timedelta(seconds=60)
            iqama_dt = self._sim_start + datetime.timedelta(seconds=10)
            entry = PrayerEntry('Maghrib', prayer_name('Maghrib', lang), adhan_dt.strftime('%H:%M'), 7, adhan_dt, iqama_dt)
            if now < iqama_dt:
                return ([entry], ActivePrayer(phase='IQAMA', prayer=entry), now)
            next_entry = PrayerEntry('Ishae', prayer_name('Ishae', lang), (now + datetime.timedelta(hours=1)).strftime('%H:%M'), 12, now + datetime.timedelta(hours=1), now + datetime.timedelta(hours=1, minutes=12))
            return ([entry, next_entry], ActivePrayer(phase='NEXT_ADHAN', prayer=next_entry), now)
        if self.simulate == 'jumaa':
            days_until_fri = (4 - now.weekday()) % 7
            sim_now = (now + datetime.timedelta(days=days_until_fri)).replace(hour=12, minute=0, second=0, microsecond=0) + datetime.timedelta(seconds=elapsed)
            dhuhr_dt = sim_now.replace(hour=12, minute=30, second=0, microsecond=0)
            iqama_dt = dhuhr_dt + datetime.timedelta(minutes=12)
            entry = PrayerEntry('Dhuhr', prayer_name('Dhuhr', lang, is_friday=True), '12:30', 12, dhuhr_dt, iqama_dt)
            return ([entry], ActivePrayer(phase='NEXT_ADHAN', prayer=entry), sim_now)
        return None

    def _on_tick(self) -> bool:
        if self._top_bar_mode:
            self._update_env_visibility()
            if self._raw_dragging and self._x11_monitor:
                ptr = self._x11_monitor.query_pointer()
                if ptr is not None:
                    expected_mask = BUTTON1_MASK if self._raw_drag_button == 1 else BUTTON2_MASK
                    if (ptr[2] & expected_mask) == 0:
                        self._finish_raw_drag(self._raw_drag_button)

        now = datetime.datetime.now()
        today = now.date()
        cfg = self.config_service.config

        if self.simulate:
            sim = self._build_simulated_state(now)
            if sim:
                self.entries, self.active, now = sim
                today = now.date()
        else:
            if self.last_fetch_date and self.last_fetch_date != today:
                self.triggered_events.clear()
                self.refresh_data(force=False)

            if not self.day_data:
                return True

            self.entries = parse_prayer_entries(self.day_data, cfg.iqama_delays, now, lang=cfg.language)
            self.active = find_active_prayer(self.entries, cfg.iqama_delays, now)

        if not self.active:
            return True

        lang = cfg.language

        # Jumu'ah (Friday) reminder check
        if cfg.friday_reminder_enabled:
            rem_min = check_jumaa_reminder(self.entries, now, cfg.friday_reminder_minutes)
            if rem_min is not None:
                jumaa_key = f'{today.isoformat()}-jumaa'
                if jumaa_key not in self.triggered_events:
                    self.triggered_events.add(jumaa_key)
                    self.system_service.notify(
                        tr(lang, 'notif_jumaa_title'),
                        tr(lang, 'notif_jumaa_body', minutes=rem_min),
                        enabled=cfg.notifications_enabled,
                    )

        phase = self.active.phase
        prayer = self.active.prayer
        ctx = self.pill.get_style_context()

        if phase == 'IQAMA':
            ctx.add_class('iqama-mode')
            self._set_icon_red(True)
            diff = (prayer.iqama_dt - now).total_seconds()
            self.name_lbl.set_text(tr(lang, 'iqama_prefix', prayer=prayer.name))
            self.time_lbl.set_text(format_countdown(diff))

            adhan_key = f'{today.isoformat()}-adhan-{prayer.key}'
            if adhan_key not in self.triggered_events and (now - prayer.adhan_dt).total_seconds() < 15:
                self.triggered_events.add(adhan_key)
                self.system_service.notify(
                    tr(lang, 'notif_adhan_title', prayer=prayer.name),
                    tr(lang, 'notif_adhan_body', prayer=prayer.name),
                    enabled=cfg.notifications_enabled,
                )
                if cfg.audio_enabled:
                    self.audio_service.play(cfg.adhan_audio_path)

            if diff <= 1:
                iqama_key = f'{today.isoformat()}-iqama-{prayer.key}'
                if iqama_key not in self.triggered_events:
                    self.triggered_events.add(iqama_key)
                    self.system_service.notify(
                        tr(lang, 'notif_iqama_title', prayer=prayer.name),
                        tr(lang, 'notif_iqama_body', prayer=prayer.name),
                        enabled=cfg.notifications_enabled,
                    )
                    self.system_service.lock_screen(
                        command=cfg.custom_lock_command,
                        enabled=cfg.lock_enabled,
                    )
        else:
            ctx.remove_class('iqama-mode')
            self._set_icon_red(False)
            diff = (prayer.adhan_dt - now).total_seconds()
            self.name_lbl.set_text(prayer.name)
            self.time_lbl.set_text(format_countdown(diff))

        if self.popup_win.get_visible():
            self.popup_win.update_hero(self.active, self.entries, now)

        return True
