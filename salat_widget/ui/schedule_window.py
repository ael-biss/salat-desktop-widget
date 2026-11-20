"""Full Monthly Prayer Schedule Window for Sala Al Jadida."""

import datetime
from typing import Optional

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

from salat_widget.constants import CITY_NAME
from salat_widget.services.prayer_service import PrayerService
from salat_widget.ui.styles import load_mosque_icon


COLUMNS = [
    ('Day', 95, False),
    ('Hijri', 64, False),
    ('Date', 96, True),
    ('Fajr', 66, True),
    ('Sunrise', 66, True),
    ('Dhuhr', 66, True),
    ('Asr', 66, True),
    ('Maghrib', 66, True),
    ('Isha', 66, True),
]


class ScheduleWindow(Gtk.Window):
    def __init__(self, prayer_service: PrayerService) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.prayer_service = prayer_service

        self.set_title(f'Monthly Prayer Schedule — {CITY_NAME}')
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
        self.title_lbl = Gtk.Label(label=f'{CITY_NAME} — Monthly Schedule', xalign=0)
        self.title_lbl.get_style_context().add_class('salat-title')
        self.sub_lbl = Gtk.Label(label='Loading schedule...', xalign=0)
        self.sub_lbl.get_style_context().add_class('salat-subtitle')
        title_col.pack_start(self.title_lbl, False, False, 0)
        title_col.pack_start(self.sub_lbl, False, False, 0)
        header.pack_start(title_col, True, True, 0)

        self.refresh_btn = Gtk.Button(label='Refresh')
        self.refresh_btn.get_style_context().add_class('salat-btn')
        self.refresh_btn.set_valign(Gtk.Align.CENTER)
        self.refresh_btn.connect('clicked', lambda *_: self.load_schedule(force=True))
        header.pack_end(self.refresh_btn, False, False, 0)

        close_btn = Gtk.Button(label='Close')
        close_btn.get_style_context().add_class('salat-btn-primary')
        close_btn.set_valign(Gtk.Align.CENTER)
        close_btn.connect('clicked', lambda *_: self.hide())
        header.pack_end(close_btn, False, False, 4)

        root.pack_start(header, False, False, 0)

        # Sticky column headers
        hdr_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr_row.get_style_context().add_class('salat-sched-header')
        for label, width, _mono in COLUMNS:
            lbl = Gtk.Label(label=label, xalign=0.5)
            lbl.set_size_request(width, -1)
            lbl.get_style_context().add_class('salat-sched-th')
            hdr_row.pack_start(lbl, True, True, 0)
        root.pack_start(hdr_row, False, False, 0)

        # Scrollable rows
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        root.pack_start(scrolled, True, True, 0)

        self.rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        scrolled.add(self.rows_box)

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def _on_delete(self, _widget, _event) -> bool:
        self.hide()
        return True

    def open_window(self) -> None:
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
            self.sub_lbl.set_text(f'Could not load schedule: {msg}')
        return False

    def _render_schedule(self, data: Optional[dict]) -> None:
        for child in self.rows_box.get_children():
            self.rows_box.remove(child)

        if not data or not isinstance(data.get('days'), list):
            lbl = Gtk.Label(label='No schedule data available. Click Refresh to fetch.')
            lbl.get_style_context().add_class('salat-hint')
            self.rows_box.pack_start(lbl, False, False, 20)
            self.rows_box.show_all()
            return

        city_label = data.get('city_label') or CITY_NAME
        hijri_month = data.get('hijri_month') or ''
        greg_period = data.get('gregorian_period') or ''
        count = data.get('days_count') or len(data['days'])

        title = f'{city_label} — {hijri_month}' if hijri_month else city_label
        self.title_lbl.set_text(title)
        self.sub_lbl.set_text(f'{greg_period} • {count} days' if greg_period else f'{count} days')

        today_iso = datetime.date.today().isoformat()

        for idx, day in enumerate(data['days']):
            d_iso = day.get('date', '')
            is_today = (d_iso == today_iso) or (bool(day.get('is_today')) and not any(x.get('date') == today_iso for x in data['days']))
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

            for col_idx, val in enumerate(values):
                _, width, is_mono = COLUMNS[col_idx]
                cell = Gtk.Label(label=val, xalign=0.5)
                cell.set_size_request(width, -1)
                cell.set_ellipsize(3)
                cell.set_tooltip_text(val)
                cell.get_style_context().add_class('salat-sched-cell-mono' if is_mono else 'salat-sched-cell')
                row.pack_start(cell, True, True, 0)

            self.rows_box.pack_start(row, False, False, 0)

        self.rows_box.show_all()
