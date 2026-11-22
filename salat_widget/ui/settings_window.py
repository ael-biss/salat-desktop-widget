"""Dedicated Settings window for configuring language, top bar, Iqama times, Jumu'ah, audio, alerts, and lock."""

import os
import time
from typing import Callable, Dict, List, Optional

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, GLib, Gtk

from salat_widget import __version__
from salat_widget.constants import (
    DEFAULT_FRIDAY_REMINDER_MINUTES,
    DEFAULT_IQAMA_DELAYS,
    PRAYER_ORDER,
)
from salat_widget.i18n import is_rtl, normalize_lang, prayer_name, tr
from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.services.update_service import UpdateService
from salat_widget.ui.styles import apply_rtl_layout, load_mosque_icon


class SettingsWindow(Gtk.Window):
    def __init__(
        self,
        config_service: ConfigService,
        audio_service: AudioService,
        update_service: UpdateService,
        on_reset_position: Callable[[], None],
        on_refresh_schedule: Callable[[], None],
        on_top_bar_mode_changed: Optional[Callable[[bool], None]] = None,
        on_top_bar_preset: Optional[Callable[[str], None]] = None,
        on_reload_app: Optional[Callable[[], None]] = None,
        on_quit_app: Optional[Callable[[], None]] = None,
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config_service = config_service
        self.audio_service = audio_service
        self.update_service = update_service
        self.on_reset_position = on_reset_position
        self.on_refresh_schedule = on_refresh_schedule
        self.on_top_bar_mode_changed = on_top_bar_mode_changed
        self.on_top_bar_preset = on_top_bar_preset
        self.on_reload_app = on_reload_app
        self.on_quit_app = on_quit_app

        self._spin_buttons: Dict[str, Gtk.SpinButton] = {}
        self._iqama_name_labels: Dict[str, Gtk.Label] = {}
        self._min_unit_labels: List[Gtk.Label] = []
        self._preset_buttons: Dict[str, Gtk.Button] = {}
        self._draft_audio_path: str = ''
        self._pending_update_url: str = ''
        self._pending_update_ver: str = ''
        self._modal_child_open: bool = False
        self._opened_at: float = 0.0

        self.set_default_size(468, 620)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class('salat-settings-window')

        self.connect('delete-event', self._on_delete)
        self.connect('key-press-event', self._on_key_press)
        self.connect('focus-out-event', self._on_focus_out)

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.add(outer)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        outer.pack_start(scrolled, True, True, 0)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        root.set_border_width(18)
        scrolled.add(root)

        # Header
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        pixbuf = load_mosque_icon(24)
        if pixbuf:
            header.pack_start(Gtk.Image.new_from_pixbuf(pixbuf), False, False, 0)
        title_col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        self.header_title_lbl = Gtk.Label(xalign=0)
        self.header_title_lbl.get_style_context().add_class('salat-title')
        self.header_sub_lbl = Gtk.Label(xalign=0)
        self.header_sub_lbl.get_style_context().add_class('salat-subtitle')
        title_col.pack_start(self.header_title_lbl, False, False, 0)
        title_col.pack_start(self.header_sub_lbl, False, False, 0)
        header.pack_start(title_col, True, True, 0)
        root.pack_start(header, False, False, 0)

        # Sections
        root.pack_start(self._build_language_section(), False, False, 0)
        root.pack_start(self._build_display_section(), False, False, 0)
        root.pack_start(self._build_iqama_section(), False, False, 0)
        root.pack_start(self._build_jumaa_section(), False, False, 0)
        root.pack_start(self._build_audio_section(), False, False, 0)
        root.pack_start(self._build_lock_section(), False, False, 0)
        root.pack_start(self._build_tools_section(), False, False, 0)

        # Sticky Footer: Cancel / Save
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.set_border_width(14)

        self.cancel_btn = Gtk.Button()
        self.cancel_btn.get_style_context().add_class('salat-btn')
        self.cancel_btn.connect('clicked', lambda *_: self._cancel_and_close())

        self.save_btn = Gtk.Button()
        self.save_btn.get_style_context().add_class('salat-btn-primary')
        self.save_btn.connect('clicked', self._on_save_clicked)

        footer.pack_end(self.save_btn, False, False, 0)
        footer.pack_end(self.cancel_btn, False, False, 0)
        outer.pack_end(footer, False, False, 0)

        self._sync_from_config()

    def _lang(self) -> str:
        return normalize_lang(self.config_service.config.language)

    def _build_language_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        self.lang_sec_title = Gtk.Label(xalign=0)
        self.lang_sec_title.get_style_context().add_class('salat-section-title')
        box.pack_start(self.lang_sec_title, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.lang_field_lbl = Gtk.Label(xalign=0)
        self.lang_field_lbl.get_style_context().add_class('salat-field-label')
        row.pack_start(self.lang_field_lbl, True, True, 0)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        btn_box.set_homogeneous(True)
        self.lang_en_btn = Gtk.Button(label='English')
        self.lang_en_btn.connect('clicked', lambda *_: self._on_language_selected('en'))
        self.lang_ar_btn = Gtk.Button(label='العربية')
        self.lang_ar_btn.connect('clicked', lambda *_: self._on_language_selected('ar'))
        btn_box.pack_start(self.lang_en_btn, True, True, 0)
        btn_box.pack_start(self.lang_ar_btn, True, True, 0)
        row.pack_end(btn_box, False, False, 0)

        box.pack_start(row, False, False, 0)
        return box

    def _on_language_selected(self, lang: str) -> None:
        norm = normalize_lang(lang)
        if self.config_service.config.language == norm:
            return
        self.config_service.config.language = norm
        self.config_service.save(notify=True)
        self.apply_language(norm)

    def _update_language_buttons(self, lang: str) -> None:
        is_ar = normalize_lang(lang) == 'ar'
        for btn, active in ((self.lang_en_btn, not is_ar), (self.lang_ar_btn, is_ar)):
            ctx = btn.get_style_context()
            ctx.remove_class('salat-btn')
            ctx.remove_class('salat-btn-primary')
            ctx.add_class('salat-btn-primary' if active else 'salat-btn')

    def _build_display_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        self.topbar_sec_title = Gtk.Label(xalign=0)
        self.topbar_sec_title.get_style_context().add_class('salat-section-title')
        box.pack_start(self.topbar_sec_title, False, False, 0)

        mode_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.topbar_mode_lbl = Gtk.Label(xalign=0)
        self.topbar_mode_lbl.get_style_context().add_class('salat-field-label')
        self.top_bar_switch = Gtk.Switch()
        self.top_bar_switch.connect('notify::active', self._on_top_bar_switch_toggled)
        mode_row.pack_start(self.topbar_mode_lbl, True, True, 0)
        mode_row.pack_end(self.top_bar_switch, False, False, 0)
        box.pack_start(mode_row, False, False, 0)

        pin_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.pin_pos_lbl = Gtk.Label(xalign=0)
        self.pin_pos_lbl.get_style_context().add_class('salat-field-label')
        self.pin_switch = Gtk.Switch()
        pin_row.pack_start(self.pin_pos_lbl, True, True, 0)
        pin_row.pack_end(self.pin_switch, False, False, 0)
        box.pack_start(pin_row, False, False, 0)

        self.topbar_hint_lbl = Gtk.Label(xalign=0)
        self.topbar_hint_lbl.set_line_wrap(True)
        self.topbar_hint_lbl.set_max_width_chars(46)
        self.topbar_hint_lbl.get_style_context().add_class('salat-hint')
        box.pack_start(self.topbar_hint_lbl, False, False, 0)

        self.preset_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.preset_row.set_homogeneous(True)
        for preset in ('left', 'right', 'far_right'):
            btn = Gtk.Button()
            btn.get_style_context().add_class('salat-btn')
            btn.connect('clicked', lambda _b, p=preset: self._on_preset_clicked(p))
            self.preset_row.pack_start(btn, True, True, 0)
            self._preset_buttons[preset] = btn
        box.pack_start(self.preset_row, False, False, 0)

        return box

    def _on_top_bar_switch_toggled(self, sw: Gtk.Switch, _pspec) -> None:
        self.preset_row.set_sensitive(sw.get_active())

    def _on_preset_clicked(self, preset: str) -> None:
        if self.on_top_bar_preset:
            self.on_top_bar_preset(preset)

    def _on_reload_clicked(self, _btn: Gtk.Button) -> None:
        self.audio_service.stop()
        self.hide()
        if self.on_reload_app:
            self.on_reload_app()

    def _on_quit_clicked(self, _btn: Gtk.Button) -> None:
        self.audio_service.stop()
        self.hide()
        if self.on_quit_app:
            self.on_quit_app()
        else:
            Gtk.main_quit()

    def _build_iqama_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.get_style_context().add_class('salat-section')

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.iqama_sec_title = Gtk.Label(xalign=0)
        self.iqama_sec_title.get_style_context().add_class('salat-section-title')
        self.reset_iqama_btn = Gtk.Button()
        self.reset_iqama_btn.get_style_context().add_class('salat-btn')
        self.reset_iqama_btn.connect('clicked', self._on_reset_iqama)
        head.pack_start(self.iqama_sec_title, True, True, 0)
        head.pack_end(self.reset_iqama_btn, False, False, 0)
        box.pack_start(head, False, False, 2)

        for key in PRAYER_ORDER:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            name_lbl = Gtk.Label(xalign=0)
            name_lbl.get_style_context().add_class('salat-field-label')
            self._iqama_name_labels[key] = name_lbl

            adj = Gtk.Adjustment(value=DEFAULT_IQAMA_DELAYS[key], lower=1, upper=120, step_increment=1, page_increment=5)
            spin = Gtk.SpinButton(adjustment=adj, numeric=True)
            spin.set_width_chars(3)
            self._spin_buttons[key] = spin

            unit_lbl = Gtk.Label(xalign=0)
            unit_lbl.get_style_context().add_class('salat-hint')
            self._min_unit_labels.append(unit_lbl)

            row.pack_start(name_lbl, True, True, 0)
            row.pack_end(unit_lbl, False, False, 2)
            row.pack_end(spin, False, False, 4)
            box.pack_start(row, False, False, 0)

        return box

    def _build_jumaa_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        self.jumaa_sec_title = Gtk.Label(xalign=0)
        self.jumaa_sec_title.get_style_context().add_class('salat-section-title')
        box.pack_start(self.jumaa_sec_title, False, False, 0)

        toggle_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.jumaa_toggle_lbl = Gtk.Label(xalign=0)
        self.jumaa_toggle_lbl.get_style_context().add_class('salat-field-label')
        self.jumaa_switch = Gtk.Switch()
        self.jumaa_switch.connect('notify::active', lambda sw, *_: self.jumaa_spin.set_sensitive(sw.get_active()))
        toggle_row.pack_start(self.jumaa_toggle_lbl, True, True, 0)
        toggle_row.pack_end(self.jumaa_switch, False, False, 0)
        box.pack_start(toggle_row, False, False, 0)

        min_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.jumaa_min_lbl = Gtk.Label(xalign=0)
        self.jumaa_min_lbl.get_style_context().add_class('salat-hint')
        adj = Gtk.Adjustment(
            value=DEFAULT_FRIDAY_REMINDER_MINUTES,
            lower=5,
            upper=240,
            step_increment=5,
            page_increment=15,
        )
        self.jumaa_spin = Gtk.SpinButton(adjustment=adj, numeric=True)
        self.jumaa_spin.set_width_chars(3)
        unit_lbl = Gtk.Label(xalign=0)
        unit_lbl.get_style_context().add_class('salat-hint')
        self._min_unit_labels.append(unit_lbl)

        min_row.pack_start(self.jumaa_min_lbl, True, True, 0)
        min_row.pack_end(unit_lbl, False, False, 2)
        min_row.pack_end(self.jumaa_spin, False, False, 4)
        box.pack_start(min_row, False, False, 0)

        return box

    def _build_audio_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        self.audio_sec_title = Gtk.Label(xalign=0)
        self.audio_sec_title.get_style_context().add_class('salat-section-title')
        box.pack_start(self.audio_sec_title, False, False, 0)

        notif_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.notif_lbl = Gtk.Label(xalign=0)
        self.notif_lbl.get_style_context().add_class('salat-field-label')
        self.notif_switch = Gtk.Switch()
        notif_row.pack_start(self.notif_lbl, True, True, 0)
        notif_row.pack_end(self.notif_switch, False, False, 0)
        box.pack_start(notif_row, False, False, 0)

        audio_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.audio_lbl = Gtk.Label(xalign=0)
        self.audio_lbl.get_style_context().add_class('salat-field-label')
        self.audio_switch = Gtk.Switch()
        audio_row.pack_start(self.audio_lbl, True, True, 0)
        audio_row.pack_end(self.audio_switch, False, False, 0)
        box.pack_start(audio_row, False, False, 0)

        self.audio_file_lbl = Gtk.Label(xalign=0)
        self.audio_file_lbl.get_style_context().add_class('salat-hint')
        box.pack_start(self.audio_file_lbl, False, False, 0)

        self.audio_path_lbl = Gtk.Label(xalign=0)
        self.audio_path_lbl.set_ellipsize(3)
        self.audio_path_lbl.get_style_context().add_class('salat-field-label')
        box.pack_start(self.audio_path_lbl, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.choose_audio_btn = Gtk.Button()
        self.choose_audio_btn.get_style_context().add_class('salat-btn')
        self.choose_audio_btn.connect('clicked', self._on_choose_audio)

        self.clear_audio_btn = Gtk.Button()
        self.clear_audio_btn.get_style_context().add_class('salat-btn')
        self.clear_audio_btn.connect('clicked', self._on_clear_audio)

        self.test_audio_btn = Gtk.Button()
        self.test_audio_btn.get_style_context().add_class('salat-btn-primary')
        self.test_audio_btn.connect('clicked', self._on_test_audio)

        btn_row.pack_start(self.choose_audio_btn, True, True, 0)
        btn_row.pack_start(self.clear_audio_btn, True, True, 0)
        btn_row.pack_start(self.test_audio_btn, True, True, 0)
        box.pack_start(btn_row, False, False, 0)

        return box

    def _build_lock_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        self.lock_sec_title = Gtk.Label(xalign=0)
        self.lock_sec_title.get_style_context().add_class('salat-section-title')
        box.pack_start(self.lock_sec_title, False, False, 0)

        lock_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.lock_toggle_lbl = Gtk.Label(xalign=0)
        self.lock_toggle_lbl.get_style_context().add_class('salat-field-label')
        self.lock_switch = Gtk.Switch()
        lock_row.pack_start(self.lock_toggle_lbl, True, True, 0)
        lock_row.pack_end(self.lock_switch, False, False, 0)
        box.pack_start(lock_row, False, False, 0)

        self.lock_cmd_lbl = Gtk.Label(xalign=0)
        self.lock_cmd_lbl.get_style_context().add_class('salat-hint')
        box.pack_start(self.lock_cmd_lbl, False, False, 0)

        self.lock_entry = Gtk.Entry()
        self.lock_entry.set_direction(Gtk.TextDirection.LTR)
        self.lock_entry.set_placeholder_text('ft_lock')
        box.pack_start(self.lock_entry, False, False, 0)

        return box

    def _build_tools_section(self) -> Gtk.Widget:
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.set_homogeneous(True)
        self.refresh_sched_btn = Gtk.Button()
        self.refresh_sched_btn.get_style_context().add_class('salat-btn')
        self.refresh_sched_btn.connect('clicked', lambda *_: self.on_refresh_schedule())

        self.reset_pos_btn = Gtk.Button()
        self.reset_pos_btn.get_style_context().add_class('salat-btn')
        self.reset_pos_btn.connect('clicked', lambda *_: self.on_reset_position())

        row.pack_start(self.refresh_sched_btn, True, True, 0)
        row.pack_start(self.reset_pos_btn, True, True, 0)
        outer.pack_start(row, False, False, 0)

        app_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        app_row.set_homogeneous(True)
        self.reload_app_btn = Gtk.Button()
        self.reload_app_btn.get_style_context().add_class('salat-btn')
        self.reload_app_btn.connect('clicked', self._on_reload_clicked)

        self.quit_app_btn = Gtk.Button()
        self.quit_app_btn.get_style_context().add_class('salat-btn')
        self.quit_app_btn.get_style_context().add_class('salat-btn-danger')
        self.quit_app_btn.connect('clicked', self._on_quit_clicked)

        app_row.pack_start(self.reload_app_btn, True, True, 0)
        app_row.pack_start(self.quit_app_btn, True, True, 0)
        outer.pack_start(app_row, False, False, 0)

        # Updates card
        upd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        upd_box.get_style_context().add_class('salat-section')
        self.update_status_lbl = Gtk.Label(xalign=0)
        self.update_status_lbl.get_style_context().add_class('salat-hint')
        self.update_btn = Gtk.Button()
        self.update_btn.get_style_context().add_class('salat-btn')
        self.update_btn.connect('clicked', self._on_update_clicked)
        upd_box.pack_start(self.update_status_lbl, True, True, 0)
        upd_box.pack_end(self.update_btn, False, False, 0)
        outer.pack_start(upd_box, False, False, 0)

        return outer

    def apply_language(self, lang: str) -> None:
        norm = normalize_lang(lang)
        ltr_keep = [self.preset_row, self.lock_entry, self.jumaa_spin, *self._spin_buttons.values()]
        apply_rtl_layout(self, is_rtl(norm), ltr_widgets=ltr_keep)
        city = tr(norm, 'city_name')

        self.set_title(tr(norm, 'settings_win_title'))
        self.header_title_lbl.set_text(tr(norm, 'widget_settings'))
        self.header_sub_lbl.set_text(tr(norm, 'settings_subtitle', city=city))

        self.lang_sec_title.set_text(tr(norm, 'sec_language'))
        self.lang_field_lbl.set_text(tr(norm, 'language_label'))
        self._update_language_buttons(norm)

        self.topbar_sec_title.set_text(tr(norm, 'sec_top_bar'))
        self.topbar_mode_lbl.set_text(tr(norm, 'dock_top_bar'))
        self.pin_pos_lbl.set_text(tr(norm, 'pin_position_toggle'))
        self.topbar_hint_lbl.set_text(tr(norm, 'top_bar_hint'))
        self._preset_buttons['left'].set_label(tr(norm, 'preset_left'))
        self._preset_buttons['right'].set_label(tr(norm, 'preset_right'))
        self._preset_buttons['far_right'].set_label(tr(norm, 'preset_far_right'))

        self.iqama_sec_title.set_text(tr(norm, 'sec_iqama'))
        self.reset_iqama_btn.set_label(tr(norm, 'reset_defaults'))
        for key, lbl in self._iqama_name_labels.items():
            lbl.set_text(prayer_name(key, lang=norm, is_friday=False))
        min_text = tr(norm, 'min_short')
        for lbl in self._min_unit_labels:
            lbl.set_text(min_text)

        self.jumaa_sec_title.set_text(tr(norm, 'sec_jumaa'))
        self.jumaa_toggle_lbl.set_text(tr(norm, 'jumaa_toggle'))
        self.jumaa_min_lbl.set_text(tr(norm, 'minutes_before_adhan'))

        self.audio_sec_title.set_text(tr(norm, 'sec_audio'))
        self.notif_lbl.set_text(tr(norm, 'desktop_notifications'))
        self.audio_lbl.set_text(tr(norm, 'play_adhan_audio'))
        self.audio_file_lbl.set_text(tr(norm, 'custom_adhan_file'))
        self.choose_audio_btn.set_label(tr(norm, 'choose_file'))
        self.clear_audio_btn.set_label(tr(norm, 'use_default'))
        self.test_audio_btn.set_label(
            tr(norm, 'stop_audio') if self.audio_service.is_playing else tr(norm, 'test_audio')
        )
        self._update_audio_label()

        self.lock_sec_title.set_text(tr(norm, 'sec_lock'))
        self.lock_toggle_lbl.set_text(tr(norm, 'lock_toggle'))
        self.lock_cmd_lbl.set_text(tr(norm, 'lock_command'))

        self.refresh_sched_btn.set_label(tr(norm, 'refresh_schedule'))
        self.reset_pos_btn.set_label(tr(norm, 'reset_position'))
        self.reload_app_btn.set_label(tr(norm, 'reload_app'))
        self.quit_app_btn.set_label(tr(norm, 'quit_app'))

        if self._pending_update_ver:
            self.update_status_lbl.set_text(tr(norm, 'update_available_lbl', version=self._pending_update_ver))
            self.update_btn.set_label(tr(norm, 'install_version', version=self._pending_update_ver))
        else:
            self.update_status_lbl.set_text(tr(norm, 'version_label', version=__version__))
            self.update_btn.set_label(tr(norm, 'check_updates'))

        self.cancel_btn.set_label(tr(norm, 'cancel'))
        self.save_btn.set_label(tr(norm, 'save'))

    def _on_update_clicked(self, _btn: Gtk.Button) -> None:
        lang = self._lang()
        if self._pending_update_url:
            self.update_btn.set_sensitive(False)
            self.update_status_lbl.set_text(tr(lang, 'downloading_update'))
            self.update_service.download_and_apply_async(
                self._pending_update_url,
                lambda ok, msg: GLib.idle_add(self._on_update_applied, ok, msg),
            )
            return

        self.update_btn.set_sensitive(False)
        self.update_status_lbl.set_text(tr(lang, 'checking_updates'))
        self.update_service.check_async(
            lambda ver, url, err: GLib.idle_add(self._on_update_checked, ver, url, err)
        )

    def _on_update_checked(self, version, url, error) -> bool:
        lang = self._lang()
        self.update_btn.set_sensitive(True)
        if error:
            self.update_status_lbl.set_text(f'v{__version__} • {error}')
        elif version and url:
            self._pending_update_url = url
            self._pending_update_ver = version
            self.update_status_lbl.set_text(tr(lang, 'update_available_lbl', version=version))
            self.update_btn.set_label(tr(lang, 'install_version', version=version))
            self.update_btn.get_style_context().add_class('salat-btn-primary')
        else:
            self.update_status_lbl.set_text(tr(lang, 'up_to_date', version=__version__))
        return False

    def _on_update_applied(self, ok: bool, msg: str) -> bool:
        lang = self._lang()
        if ok:
            self.update_status_lbl.set_text(tr(lang, 'updated_restarting'))
            GLib.timeout_add(400, self.update_service.restart_installed)
        else:
            self.update_btn.set_sensitive(True)
            self.update_status_lbl.set_text(tr(lang, 'update_failed', msg=msg))
        return False

    def _sync_from_config(self) -> None:
        cfg = self.config_service.config
        self.top_bar_switch.set_active(cfg.top_bar_mode)
        self.pin_switch.set_active(cfg.position_locked)
        self.preset_row.set_sensitive(cfg.top_bar_mode)
        for key, spin in self._spin_buttons.items():
            spin.set_value(cfg.iqama_delays.get(key, DEFAULT_IQAMA_DELAYS[key]))
        self.notif_switch.set_active(cfg.notifications_enabled)
        self.jumaa_switch.set_active(cfg.friday_reminder_enabled)
        self.jumaa_spin.set_value(cfg.friday_reminder_minutes)
        self.jumaa_spin.set_sensitive(cfg.friday_reminder_enabled)
        self.audio_switch.set_active(cfg.audio_enabled)
        self.lock_switch.set_active(cfg.lock_enabled)
        self.lock_entry.set_text(cfg.custom_lock_command or 'ft_lock')
        self._draft_audio_path = cfg.adhan_audio_path or ''
        self.apply_language(cfg.language)

    def _update_audio_label(self) -> None:
        custom = self._draft_audio_path.strip()
        if custom:
            self.audio_path_lbl.set_text(os.path.basename(custom))
            self.audio_path_lbl.set_tooltip_text(custom)
        else:
            self.audio_path_lbl.set_text(tr(self._lang(), 'default_audio_label'))
            self.audio_path_lbl.set_tooltip_text('')

    def _on_reset_iqama(self, _btn: Gtk.Button) -> None:
        for key, spin in self._spin_buttons.items():
            spin.set_value(DEFAULT_IQAMA_DELAYS[key])

    def _on_choose_audio(self, _btn: Gtk.Button) -> None:
        lang = self._lang()
        dialog = Gtk.FileChooserDialog(
            title=tr(lang, 'select_audio_title'),
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL,
            Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN,
            Gtk.ResponseType.OK,
        )
        audio_filter = Gtk.FileFilter()
        audio_filter.set_name(tr(lang, 'audio_filter_name'))
        for pattern in ('*.mp3', '*.wav', '*.ogg', '*.flac', '*.m4a', '*.aac'):
            audio_filter.add_pattern(pattern)
        dialog.add_filter(audio_filter)

        self._modal_child_open = True
        try:
            if dialog.run() == Gtk.ResponseType.OK:
                self._draft_audio_path = dialog.get_filename() or ''
                self._update_audio_label()
        finally:
            dialog.destroy()
            self._opened_at = time.monotonic()
            self._modal_child_open = False

    def _on_clear_audio(self, _btn: Gtk.Button) -> None:
        self._draft_audio_path = ''
        self._update_audio_label()

    def _on_test_audio(self, _btn: Gtk.Button) -> None:
        lang = self._lang()
        if self.audio_service.is_playing:
            self.audio_service.stop()
            self.test_audio_btn.set_label(tr(lang, 'test_audio'))
        else:
            ok = self.audio_service.play(self._draft_audio_path)
            if ok:
                self.test_audio_btn.set_label(tr(lang, 'stop_audio'))

    def _on_save_clicked(self, _btn: Gtk.Button) -> None:
        cfg = self.config_service.config
        prev_top_bar_mode = cfg.top_bar_mode

        for key, spin in self._spin_buttons.items():
            cfg.iqama_delays[key] = int(spin.get_value())

        cfg.top_bar_mode = self.top_bar_switch.get_active()
        cfg.position_locked = self.pin_switch.get_active()
        cfg.notifications_enabled = self.notif_switch.get_active()
        cfg.friday_reminder_enabled = self.jumaa_switch.get_active()
        cfg.friday_reminder_minutes = int(self.jumaa_spin.get_value())
        cfg.audio_enabled = self.audio_switch.get_active()
        cfg.adhan_audio_path = self._draft_audio_path
        cfg.lock_enabled = self.lock_switch.get_active()
        cfg.custom_lock_command = self.lock_entry.get_text().strip() or 'ft_lock'

        self.audio_service.stop()
        self.test_audio_btn.set_label(tr(cfg.language, 'test_audio'))
        self.hide()

        if cfg.top_bar_mode != prev_top_bar_mode and self.on_top_bar_mode_changed:
            self.config_service.save(notify=False)
            GLib.idle_add(self.on_top_bar_mode_changed, cfg.top_bar_mode)
        else:
            self.config_service.save(notify=True)

    @property
    def is_modal_open(self) -> bool:
        return self._modal_child_open

    def _on_focus_out(self, _widget, _event) -> bool:
        if self._modal_child_open or not self.get_visible():
            return False
        if (time.monotonic() - self._opened_at) < 0.15:
            return False
        self._cancel_and_close()
        return False

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self._cancel_and_close()
            return True
        return False

    def _on_delete(self, _widget, _event) -> bool:
        self._cancel_and_close()
        return True

    def close_window(self) -> None:
        self._cancel_and_close()

    def _cancel_and_close(self) -> None:
        self.audio_service.stop()
        self.test_audio_btn.set_label(tr(self._lang(), 'test_audio'))
        self.hide()

    def open_window(self) -> None:
        self._opened_at = time.monotonic()
        self._sync_from_config()
        self.show_all()
        self.present()
