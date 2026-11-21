"""Full Monthly Prayer Schedule Window for Sala Al Jadida."""

import datetime
from typing import List, Optional

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

from salat_widget.i18n import is_rtl, tr
from salat_widget.services.config_service import ConfigService
from salat_widget.services.prayer_service import PrayerService
from salat_widget.ui.styles import apply_rtl_layout, load_mosque_icon


COLUMNS = [
    ('col_day', 95, False),
    ('col_hijri', 64, False),
    ('col_date', 96, True),
    ('col_fajr', 66, True),
    ('col_sunrise', 66, True),
    ('col_dhuhr', 66, True),
    ('col_asr', 66, True),
    ('col_maghrib', 66, True),
    ('col_isha', 66, True),
]


class ScheduleWindow(Gtk.Window):
    def __init__(
        self,
        prayer_service: PrayerService,
        config_service: Optional[ConfigService] = None,
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.prayer_service = prayer_service
        self.config_service = config_service
        self._last_data: Optional[dict] = None
        self._col_labels: List[Gtk.Label] = []

        self.set_default_size(760, 560)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class('salat-settings-window')

        self.connect('delete-event', self._on_delete)
        self.connect('key-press-event', self._on_key_press)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_border_width(18)
        self.add(root)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pixbuf = load_mosque_icon(24)
        if pixbuf:
            header.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)

        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.title_lbl = Gtk.Label(xalign=0)
        self.title_lbl.get_style_context().add_class('salat-title')
        self.sub_lbl = Gtk.Label(xalign=0)
        self.sub_lbl.get_style_context().add_class('salat-subtitle')
        title_col.pack_start(self.title_lbl, False, False, 0)
        title_col.pack_start(self.sub_lbl, False, False, 0)
        header.pack_start(title_col, True, True, 0)

        self.refresh_btn = Gtk.Button()
        self.refresh_btn.get_style_context().add_class('salat-btn')
        self.refresh_btn.set_valign(Gtk.Align.CENTER)
        self.refresh_btn.connect('clicked', lambda *_: self.load_schedule(force=True))
        header.pack_end(self.refresh_btn, False, False, 0)

        self.close_btn = Gtk.Button()
        self.close_btn.get_style_context().add_class('salat-btn-primary')
        self.close_btn.set_valign(Gtk.Align.CENTER)
        self.close_btn.connect('clicked', lambda *_: self.hide())
        header.pack_end(self.close_btn, False, False, 4)

        root.pack_start(header, False, False, 0)

        # Sticky column headers
        hdr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr_row.get_style_context().add_class('salat-sched-header')
        for _key, width, _mono in COLUMNS:
            lbl = Gtk.Label(xalign=0.5)
            lbl.set_size_request(width, -1)
            lbl.get_style_context().add_class('salat-sched-th')
            hdr_row.pack_start(lbl, True, True, 0)
            self._col_labels.append(lbl)
        root.pack_start(hdr_row, False, False, 0)

        # Scrollable rows
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        root.pack_start(scrolled, True, True, 0)

        self.rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        scrolled.add(self.rows_box)

        self.apply_language(self._lang())

    def _lang(self) -> str:
        return self.config_service.config.language if self.config_service else 'en'

    def apply_language(self, lang: str) -> None:
        apply_rtl_layout(self, is_rtl(lang))
        city = tr(lang, 'city_name')
        self.set_title(tr(lang, 'monthly_win_title', city=city))
        self.refresh_btn.set_label(tr(lang, 'refresh'))
        self.close_btn.set_label(tr(lang, 'close'))
        for lbl, (key, _width, _mono) in zip(self._col_labels, COLUMNS):
            lbl.set_text(tr(lang, key))
        if self._last_data is not None:
            self._render_schedule(self._last_data)
        else:
            self.title_lbl.set_text(tr(lang, 'monthly_header_default', city=city))
            self.sub_lbl.set_text(tr(lang, 'loading_monthly'))

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def _on_delete(self, _widget, _event) -> bool:
        self.hide()
        return True

    def open_window(self) -> None:
        self.apply_language(self._lang())
        self.show_all()
        self.present()
        self.load_schedule(force=False)

    def load_schedule(self, force: bool = False) -> None:
        self.refresh_btn.set_sensitive(False)
        cached = self.prayer_service.get_monthly_schedule()
        if cached and not force:
            self._render_schedule(cached)

        def on_success(data: dict) -> None:
            GLib.idle_add(self._on_loaded, data)

        def on_error(msg: str) -> None:
            GLib.idle_add(self._on_error, msg)

        self.prayer_service.fetch_monthly_async(force=force, on_success=on_success, on_error=on_error)

    def _on_loaded(self, data: dict) -> bool:
        self._render_schedule(data)
        self.refresh_btn.set_sensitive(True)
        return False

    def _on_error(self, msg: str) -> bool:
        self.refresh_btn.set_sensitive(True)
        if not self.rows_box.get_children():
            self.sub_lbl.set_text(tr(self._lang(), 'could_not_load', msg=msg))
        return False

    def _render_schedule(self, data: Optional[dict]) -> None:
        self._last_data = data
        lang = self._lang()
        for child in self.rows_box.get_children():
            self.rows_box.remove(child)

        if not data or not isinstance(data.get('days'), list):
            lbl = Gtk.Label(label=tr(lang, 'no_schedule_data'))
            lbl.get_style_context().add_class('salat-hint')
            self.rows_box.pack_start(lbl, False, False, 20)
            self.rows_box.show_all()
            return

        city_label = data.get('city_label') or tr(lang, 'city_name')
        hijri_month = data.get('hijri_month') or ''
        greg_period = data.get('gregorian_period') or ''
        count = data.get('days_count') or len(data['days'])

        title = f'{city_label} — {hijri_month}' if hijri_month else city_label
        self.title_lbl.set_text(title)
        days_text = tr(lang, 'days_count', count=count)
        self.sub_lbl.set_text(f'{greg_period} • {days_text}' if greg_period else days_text)

        today_iso = datetime.date.today().isoformat()

        for idx, day in enumerate(data['days']):
            d_iso = day.get('date', '')
            is_today = (d_iso == today_iso) or (
                bool(day.get('is_today')) and not any(x.get('date') == today_iso for x in data['days'])
            )
            is_past = bool(d_iso) and d_iso < today_iso

            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            row_ctx = row.get_style_context()
            row_ctx.add_class('salat-sched-row')
            if is_today:
                row_ctx.add_class('salat-sched-row-today')
            else:
                if idx % 2 == 1:
                    row_ctx.add_class('salat-sched-row-alt')
                if is_past:
                    row_ctx.add_class('salat-sched-row-past')

            day_ar = day.get('day_ar', '')
            if is_today:
                day_ar = f'★ {day_ar}'

            values = [
                day_ar,
                str(day.get('hijri_day', '')),
                d_iso,
                day.get('fajr', ''),
                day.get('sunrise', ''),
                day.get('dhuhr', ''),
                day.get('asr', ''),
                day.get('maghrib', ''),
                day.get('isha', ''),
            ]

            ltr_cells = []
            for col_idx, val in enumerate(values):
                _, width, is_mono = COLUMNS[col_idx]
                cell = Gtk.Label(label=val, xalign=0.5)
                if is_mono:
                    ltr_cells.append(cell)
                cell.set_size_request(width, -1)
                cell.set_ellipsize(3)
                cell.set_tooltip_text(val)
                cell.get_style_context().add_class('salat-sched-cell-mono' if is_mono else 'salat-sched-cell')
                row.pack_start(cell, True, True, 0)

            apply_rtl_layout(row, is_rtl(lang), ltr_widgets=ltr_cells)
            self.rows_box.pack_start(row, False, False, 0)

        self.rows_box.show_all()
