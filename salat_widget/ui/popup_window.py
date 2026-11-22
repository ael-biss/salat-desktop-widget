"""Schedule popup window anchored near the floating desktop pill."""

import datetime
import time
from typing import Callable, Dict, List, Optional

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk

from salat_widget.constants import DEFAULT_IQAMA_DELAYS, DISPLAY_ORDER
from salat_widget.core.calculator import calculate_progress, format_countdown
from salat_widget.i18n import format_date, is_rtl, prayer_name, tr
from salat_widget.models import ActivePrayer, PrayerEntry
from salat_widget.services.config_service import ConfigService
from salat_widget.ui.styles import apply_rtl_layout, enable_rgba, load_mosque_icon


class PopupWindow(Gtk.Window):
    def __init__(
        self,
        config_service: ConfigService,
        on_open_settings: Callable[[], None],
        on_open_schedule: Callable[[], None],
        on_refresh: Callable[[], None],
        on_reload: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config_service = config_service
        self.on_open_settings = on_open_settings
        self.on_open_schedule = on_open_schedule
        self.on_refresh = on_refresh
        self.on_reload = on_reload
        self.on_quit = on_quit
        self._opened_at: float = 0.0

        self.get_style_context().add_class('salat-transparent')
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_resizable(False)
        self.stick()
        enable_rgba(self)

        self.connect('key-press-event', self._on_key_press)
        self.connect('focus-out-event', self._on_focus_out)

        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        card.get_style_context().add_class('salat-card')
        card.set_size_request(308, -1)
        self.add(card)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self._icon_green = load_mosque_icon(22, red=False)
        self._icon_red = load_mosque_icon(22, red=True)
        self._is_red_icon = False
        self.header_icon = Gtk.Image()
        if self._icon_green:
            self.header_icon.set_from_pixbuf(self._icon_green)
            header.pack_start(self.header_icon, False, False, 0)

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        self.title_lbl = Gtk.Label(xalign=0)
        self.title_lbl.get_style_context().add_class('salat-title')
        self.sub_lbl = Gtk.Label(xalign=0)
        self.sub_lbl.get_style_context().add_class('salat-subtitle')
        title_col.pack_start(self.title_lbl, False, False, 0)
        title_col.pack_start(self.sub_lbl, False, False, 0)
        header.pack_start(title_col, True, True, 0)

        close_btn = Gtk.Button(label='✕')
        close_btn.get_style_context().add_class('salat-close-btn')
        close_btn.set_valign(Gtk.Align.START)
        close_btn.connect('clicked', lambda *_: self.hide())
        header.pack_end(close_btn, False, False, 0)
        card.pack_start(header, False, False, 0)

        # Hero Next-Prayer Banner
        self.hero_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.hero_card.get_style_context().add_class('salat-hero-card')

        self.hero_badge = Gtk.Label(xalign=0)
        self.hero_badge.get_style_context().add_class('salat-hero-badge')
        self.hero_card.pack_start(self.hero_badge, False, False, 0)

        hero_mid = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.hero_name = Gtk.Label(label='--', xalign=0)
        self.hero_name.get_style_context().add_class('salat-hero-name')
        self.hero_countdown = Gtk.Label(label='--:--:--', xalign=1)
        self.hero_countdown.set_direction(Gtk.TextDirection.LTR)
        self.hero_countdown.get_style_context().add_class('salat-hero-countdown')
        hero_mid.pack_start(self.hero_name, True, True, 0)
        hero_mid.pack_end(self.hero_countdown, False, False, 0)
        self.hero_card.pack_start(hero_mid, False, False, 0)

        self.hero_progress = Gtk.ProgressBar()
        self.hero_progress.get_style_context().add_class('salat-progress')
        self.hero_progress.set_fraction(0.25)
        self.hero_card.pack_start(self.hero_progress, False, False, 2)
        card.pack_start(self.hero_card, False, False, 0)

        # Prayer Table
        self.table_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        self.table_box.get_style_context().add_class('salat-table-box')
        card.pack_start(self.table_box, False, False, 0)

        # Full Schedule button
        self.schedule_btn = Gtk.Button()
        self.schedule_btn.get_style_context().add_class('salat-btn')
        self.schedule_btn.connect('clicked', self._on_schedule_clicked)
        card.pack_start(self.schedule_btn, False, False, 0)

        # Pin / Unpin Position toggle button
        self.pin_btn = Gtk.Button()
        self.pin_btn.get_style_context().add_class('salat-btn')
        self.pin_btn.connect('clicked', self._on_pin_clicked)
        card.pack_start(self.pin_btn, False, False, 0)

        # Footer actions (2x2 clean grid: Settings / Refresh + Reload / Quit)
        actions_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions_top.set_homogeneous(True)

        self.settings_btn = Gtk.Button()
        self.settings_btn.get_style_context().add_class('salat-btn-primary')
        self.settings_btn.connect('clicked', self._on_settings_clicked)

        self.refresh_btn = Gtk.Button()
        self.refresh_btn.get_style_context().add_class('salat-btn')
        self.refresh_btn.connect('clicked', lambda *_: self.on_refresh())

        actions_top.pack_start(self.settings_btn, True, True, 0)
        actions_top.pack_start(self.refresh_btn, True, True, 0)
        card.pack_start(actions_top, False, False, 0)

        actions_bottom = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions_bottom.set_homogeneous(True)

        self.reload_btn = Gtk.Button()
        self.reload_btn.get_style_context().add_class('salat-btn')
        self.reload_btn.connect('clicked', self._on_reload_clicked)

        self.quit_btn = Gtk.Button()
        self.quit_btn.get_style_context().add_class('salat-btn')
        self.quit_btn.get_style_context().add_class('salat-btn-danger')
        self.quit_btn.connect('clicked', self._on_quit_clicked)

        actions_bottom.pack_start(self.reload_btn, True, True, 0)
        actions_bottom.pack_start(self.quit_btn, True, True, 0)
        card.pack_start(actions_bottom, False, False, 0)

        self.apply_language(self.config_service.config.language)

    def _lang(self) -> str:
        return self.config_service.config.language

    def apply_language(self, lang: str) -> None:
        apply_rtl_layout(self, is_rtl(lang), ltr_widgets=(self.hero_countdown,))
        self.title_lbl.set_text(tr(lang, 'city_name'))
        self.schedule_btn.set_label(tr(lang, 'view_monthly_schedule'))
        self.settings_btn.set_label(tr(lang, 'settings'))
        self.refresh_btn.set_label(tr(lang, 'refresh'))
        self.reload_btn.set_label(tr(lang, 'reload_app'))
        self.quit_btn.set_label(tr(lang, 'quit'))
        self._update_pin_button()
        if not self.hero_badge.get_text():
            self.hero_badge.set_text(tr(lang, 'next_prayer'))

    def _update_pin_button(self) -> None:
        pinned = self.config_service.config.position_locked
        lang = self._lang()
        self.pin_btn.set_label(tr(lang, 'unpin_btn' if pinned else 'pin_btn'))
        ctx = self.pin_btn.get_style_context()
        if pinned:
            ctx.add_class('salat-btn-pinned')
        else:
            ctx.remove_class('salat-btn-pinned')

    def _on_pin_clicked(self, _btn: Gtk.Button) -> None:
        self.config_service.config.position_locked = not self.config_service.config.position_locked
        self.config_service.save(notify=True)
        self._update_pin_button()

    def _on_focus_out(self, _widget, _event) -> bool:
        if not self.get_visible() or (time.monotonic() - self._opened_at) < 0.15:
            return False
        self.hide()
        return False

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def _on_settings_clicked(self, _btn: Gtk.Button) -> None:
        self.hide()
        self.on_open_settings()

    def _on_schedule_clicked(self, _btn: Gtk.Button) -> None:
        self.hide()
        self.on_open_schedule()

    def _on_reload_clicked(self, _btn: Gtk.Button) -> None:
        self.hide()
        if self.on_reload:
            self.on_reload()

    def _on_quit_clicked(self, _btn: Gtk.Button) -> None:
        self.hide()
        if self.on_quit:
            self.on_quit()
        else:
            Gtk.main_quit()

    def update_hero(
        self,
        active: Optional[ActivePrayer],
        entries: List[PrayerEntry],
        now: datetime.datetime,
    ) -> None:
        if not active:
            return
        lang = self._lang()
        ctx = self.hero_card.get_style_context()
        is_iqama = active.phase == 'IQAMA'
        if is_iqama:
            ctx.add_class('iqama-mode')
            self.hero_badge.set_text(tr(lang, 'iqama_countdown'))
            diff = (active.prayer.iqama_dt - now).total_seconds()
        else:
            ctx.remove_class('iqama-mode')
            self.hero_badge.set_text(tr(lang, 'next_prayer'))
            diff = (active.prayer.adhan_dt - now).total_seconds()

        if is_iqama != self._is_red_icon:
            self._is_red_icon = is_iqama
            pixbuf = self._icon_red if is_iqama else self._icon_green
            if pixbuf:
                self.header_icon.set_from_pixbuf(pixbuf)

        self.hero_name.set_text(active.prayer.name)
        self.hero_countdown.set_text(format_countdown(diff))
        self.hero_progress.set_fraction(calculate_progress(active, entries, now))

    def update_content(
        self,
        day_data: Optional[Dict[str, str]],
        active: Optional[ActivePrayer],
        entries: List[PrayerEntry],
        now: datetime.datetime,
    ) -> None:
        lang = self._lang()
        self.apply_language(lang)
        self._update_pin_button()
        self.sub_lbl.set_text(format_date(now, lang))
        self.update_hero(active, entries, now)

        for child in self.table_box.get_children():
            self.table_box.remove(child)

        if not day_data:
            lbl = Gtk.Label(label=tr(lang, 'loading_schedule'))
            lbl.get_style_context().add_class('salat-hint')
            self.table_box.pack_start(lbl, False, False, 12)
            self.table_box.show_all()
            return

        active_key = active.prayer.key if active else None
        is_iqama = bool(active and active.phase == 'IQAMA')
        is_friday = now.weekday() == 4
        delays = self.config_service.config.iqama_delays

        ltr_times = []
        for key in DISPLAY_ORDER:
            time_str = day_data.get(key, '--:--')
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            row.get_style_context().add_class('salat-row')
            if key == active_key:
                row.get_style_context().add_class('salat-row-active')
                if is_iqama:
                    row.get_style_context().add_class('iqama-mode')

            display_name = prayer_name(key, lang=lang, is_friday=is_friday)
            name_lbl = Gtk.Label(label=display_name, xalign=0)
            name_lbl.get_style_context().add_class('salat-row-name')
            row.pack_start(name_lbl, True, True, 0)

            time_lbl = Gtk.Label(label=time_str, xalign=1)
            time_lbl.get_style_context().add_class('salat-row-time')
            ltr_times.append(time_lbl)
            row.pack_end(time_lbl, False, False, 0)

            if key in DEFAULT_IQAMA_DELAYS:
                delay_min = delays.get(key, DEFAULT_IQAMA_DELAYS[key])
                iq_lbl = Gtk.Label(label=tr(lang, 'iqama_pill', minutes=delay_min), xalign=1)
                iq_lbl.get_style_context().add_class('salat-iqama-pill')
                row.pack_end(iq_lbl, False, False, 4)

            self.table_box.pack_start(row, False, False, 0)

        apply_rtl_layout(self.table_box, is_rtl(lang), ltr_widgets=ltr_times)
        self.table_box.show_all()

    def position_near(self, anchor_window: Gtk.Window) -> None:
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geo = monitor.get_geometry()
        wa = monitor.get_workarea()
        panel_bottom = wa.y if wa.y > geo.y else geo.y + 28

        if hasattr(anchor_window, 'get_screen_rect'):
            px, py, pw, ph = anchor_window.get_screen_rect()
        else:
            px, py = anchor_window.get_position()
            pw, ph = anchor_window.get_size()
        mw, mh = self.get_size()

        # Center horizontally beneath the pill, clamped to monitor bounds
        centered_x = px + (pw - mw) // 2
        target_x = max(geo.x + 8, min(centered_x, geo.x + geo.width - mw - 8))
        target_y = max(panel_bottom + 6, py + ph + 8)
        if target_y + mh > geo.y + geo.height - 8:
            target_y = max(panel_bottom + 6, py - mh - 8)
        self.move(target_x, target_y)

    def toggle_near(
        self,
        anchor_window: Gtk.Window,
        day_data: Optional[Dict[str, str]],
        active: Optional[ActivePrayer],
        entries: List[PrayerEntry],
    ) -> None:
        if self.get_visible():
            self.hide()
            return
        self.update_content(day_data, active, entries, datetime.datetime.now())
        self._opened_at = time.monotonic()
        self.show_all()
        self.position_near(anchor_window)
        self.present()
