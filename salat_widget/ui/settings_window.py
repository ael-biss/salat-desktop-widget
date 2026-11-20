"""Dedicated Settings window for configuring Iqama times, Jumu'ah, audio, alerts, and lock."""

import os
from typing import Callable, Dict

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gdk, Gtk

from salat_widget.constants import (
    CITY_NAME,
    DEFAULT_FRIDAY_REMINDER_MINUTES,
    DEFAULT_IQAMA_DELAYS,
    PRAYER_LABELS,
    PRAYER_ORDER,
)
from salat_widget.services.audio_service import AudioService
from salat_widget.services.config_service import ConfigService
from salat_widget.ui.styles import load_mosque_icon


class SettingsWindow(Gtk.Window):
    def __init__(
        self,
        config_service: ConfigService,
        audio_service: AudioService,
        on_reset_position: Callable[[], None],
        on_refresh_schedule: Callable[[], None],
        on_overlay_changed: Callable[[bool], None],
    ) -> None:
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.config_service = config_service
        self.audio_service = audio_service
        self.on_reset_position = on_reset_position
        self.on_refresh_schedule = on_refresh_schedule
        self.on_overlay_changed = on_overlay_changed
        self._spin_buttons: Dict[str, Gtk.SpinButton] = {}
        self._draft_audio_path: str = ''

        self.set_title('Salat Widget Settings')
        self.set_default_size(468, 600)
        self.set_resizable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.get_style_context().add_class('salat-settings-window')

        self.connect('delete-event', self._on_delete)
        self.connect('key-press-event', self._on_key_press)

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
        title_lbl = Gtk.Label(label='Widget Settings', xalign=0)
        title_lbl.get_style_context().add_class('salat-title')
        sub_lbl = Gtk.Label(label=f'City: {CITY_NAME} • Click Save to apply changes', xalign=0)
        sub_lbl.get_style_context().add_class('salat-subtitle')
        title_col.pack_start(title_lbl, False, False, 0)
        title_col.pack_start(sub_lbl, False, False, 0)
        header.pack_start(title_col, True, True, 0)
        root.pack_start(header, False, False, 0)

        # Sections
        root.pack_start(self._build_iqama_section(), False, False, 0)
        root.pack_start(self._build_jumaa_section(), False, False, 0)
        root.pack_start(self._build_audio_section(), False, False, 0)
        root.pack_start(self._build_lock_section(), False, False, 0)
        root.pack_start(self._build_display_section(), False, False, 0)
        root.pack_start(self._build_tools_section(), False, False, 0)

        # Sticky Footer: Cancel / Save
        footer = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        footer.set_border_width(14)

        cancel_btn = Gtk.Button(label='Cancel')
        cancel_btn.get_style_context().add_class('salat-btn')
        cancel_btn.connect('clicked', lambda *_: self._cancel_and_close())

        save_btn = Gtk.Button(label='Save')
        save_btn.get_style_context().add_class('salat-btn-primary')
        save_btn.connect('clicked', self._on_save_clicked)

        footer.pack_end(save_btn, False, False, 0)
        footer.pack_end(cancel_btn, False, False, 0)
        outer.pack_end(footer, False, False, 0)

        self._sync_from_config()

    def _build_iqama_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.get_style_context().add_class('salat-section')

        head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label='IQAMA DELAYS (MINUTES)', xalign=0)
        lbl.get_style_context().add_class('salat-section-title')
        reset_btn = Gtk.Button(label='Reset Defaults')
        reset_btn.get_style_context().add_class('salat-btn')
        reset_btn.connect('clicked', self._on_reset_iqama)
        head.pack_start(lbl, True, True, 0)
        head.pack_end(reset_btn, False, False, 0)
        box.pack_start(head, False, False, 2)

        for key in PRAYER_ORDER:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            name_lbl = Gtk.Label(label=PRAYER_LABELS[key], xalign=0)
            name_lbl.get_style_context().add_class('salat-field-label')

            adj = Gtk.Adjustment(value=DEFAULT_IQAMA_DELAYS[key], lower=1, upper=120, step_increment=1, page_increment=5)
            spin = Gtk.SpinButton(adjustment=adj, numeric=True)
            spin.set_width_chars(3)
            self._spin_buttons[key] = spin

            unit_lbl = Gtk.Label(label='min', xalign=0)
            unit_lbl.get_style_context().add_class('salat-hint')

            row.pack_start(name_lbl, True, True, 0)
            row.pack_end(unit_lbl, False, False, 2)
            row.pack_end(spin, False, False, 4)
            box.pack_start(row, False, False, 0)

        return box

    def _build_jumaa_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        title = Gtk.Label(label="JUMU'AH (FRIDAY) REMINDER", xalign=0)
        title.get_style_context().add_class('salat-section-title')
        box.pack_start(title, False, False, 0)

        toggle_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        toggle_lbl = Gtk.Label(label="Remind before Jumu'ah prayer", xalign=0)
        toggle_lbl.get_style_context().add_class('salat-field-label')
        self.jumaa_switch = Gtk.Switch()
        self.jumaa_switch.connect('notify::active', lambda sw, *_: self.jumaa_spin.set_sensitive(sw.get_active()))
        toggle_row.pack_start(toggle_lbl, True, True, 0)
        toggle_row.pack_end(self.jumaa_switch, False, False, 0)
        box.pack_start(toggle_row, False, False, 0)

        min_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        min_lbl = Gtk.Label(label='Minutes before Adhan', xalign=0)
        min_lbl.get_style_context().add_class('salat-hint')
        adj = Gtk.Adjustment(
            value=DEFAULT_FRIDAY_REMINDER_MINUTES,
            lower=5,
            upper=240,
            step_increment=5,
            page_increment=15,
        )
        self.jumaa_spin = Gtk.SpinButton(adjustment=adj, numeric=True)
        self.jumaa_spin.set_width_chars(3)
        unit_lbl = Gtk.Label(label='min', xalign=0)
        unit_lbl.get_style_context().add_class('salat-hint')

        min_row.pack_start(min_lbl, True, True, 0)
        min_row.pack_end(unit_lbl, False, False, 2)
        min_row.pack_end(self.jumaa_spin, False, False, 4)
        box.pack_start(min_row, False, False, 0)

        return box

    def _build_audio_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        title = Gtk.Label(label='AUDIO & NOTIFICATIONS', xalign=0)
        title.get_style_context().add_class('salat-section-title')
        box.pack_start(title, False, False, 0)

        notif_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        notif_lbl = Gtk.Label(label='Desktop Notifications', xalign=0)
        notif_lbl.get_style_context().add_class('salat-field-label')
        self.notif_switch = Gtk.Switch()
        notif_row.pack_start(notif_lbl, True, True, 0)
        notif_row.pack_end(self.notif_switch, False, False, 0)
        box.pack_start(notif_row, False, False, 0)

        audio_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        audio_lbl = Gtk.Label(label='Play Adhan Audio', xalign=0)
        audio_lbl.get_style_context().add_class('salat-field-label')
        self.audio_switch = Gtk.Switch()
        audio_row.pack_start(audio_lbl, True, True, 0)
        audio_row.pack_end(self.audio_switch, False, False, 0)
        box.pack_start(audio_row, False, False, 0)

        file_lbl = Gtk.Label(label='Custom Adhan File (optional)', xalign=0)
        file_lbl.get_style_context().add_class('salat-hint')
        box.pack_start(file_lbl, False, False, 0)

        self.audio_path_lbl = Gtk.Label(label='Default (assets/adan.mp3)', xalign=0)
        self.audio_path_lbl.set_ellipsize(3)
        self.audio_path_lbl.get_style_context().add_class('salat-field-label')
        box.pack_start(self.audio_path_lbl, False, False, 0)

        btn_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        choose_btn = Gtk.Button(label='Choose File...')
        choose_btn.get_style_context().add_class('salat-btn')
        choose_btn.connect('clicked', self._on_choose_audio)

        clear_btn = Gtk.Button(label='Use Default')
        clear_btn.get_style_context().add_class('salat-btn')
        clear_btn.connect('clicked', self._on_clear_audio)

        self.test_audio_btn = Gtk.Button(label='Test Audio')
        self.test_audio_btn.get_style_context().add_class('salat-btn-primary')
        self.test_audio_btn.connect('clicked', self._on_test_audio)

        btn_row.pack_start(choose_btn, True, True, 0)
        btn_row.pack_start(clear_btn, True, True, 0)
        btn_row.pack_start(self.test_audio_btn, True, True, 0)
        box.pack_start(btn_row, False, False, 0)

        return box

    def _build_lock_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('salat-section')

        title = Gtk.Label(label='AUTO-LOCK ON IQAMA', xalign=0)
        title.get_style_context().add_class('salat-section-title')
        box.pack_start(title, False, False, 0)

        lock_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lock_lbl = Gtk.Label(label='Lock screen when Iqama starts', xalign=0)
        lock_lbl.get_style_context().add_class('salat-field-label')
        self.lock_switch = Gtk.Switch()
        lock_row.pack_start(lock_lbl, True, True, 0)
        lock_row.pack_end(self.lock_switch, False, False, 0)
        box.pack_start(lock_row, False, False, 0)

        cmd_lbl = Gtk.Label(label='Lock Command', xalign=0)
        cmd_lbl.get_style_context().add_class('salat-hint')
        box.pack_start(cmd_lbl, False, False, 0)

        self.lock_entry = Gtk.Entry()
        self.lock_entry.set_placeholder_text('ft_lock')
        box.pack_start(self.lock_entry, False, False, 0)

        return box

    def _build_display_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.get_style_context().add_class('salat-section')

        title = Gtk.Label(label='DISPLAY & OVERVIEW', xalign=0)
        title.get_style_context().add_class('salat-section-title')
        box.pack_start(title, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        lbl = Gtk.Label(label='Stay visible in Activities Overview', xalign=0)
        lbl.get_style_context().add_class('salat-field-label')
        self.overlay_switch = Gtk.Switch()
        row.pack_start(lbl, True, True, 0)
        row.pack_end(self.overlay_switch, False, False, 0)
        box.pack_start(row, False, False, 0)

        hint = Gtk.Label(
            label='Keeps the pill visible when pressing Super (Overview). Kept just below the top bar so clicks are never blocked by GNOME.',
            xalign=0,
        )
        hint.set_line_wrap(True)
        hint.get_style_context().add_class('salat-hint')
        box.pack_start(hint, False, False, 0)

        return box

    def _build_tools_section(self) -> Gtk.Widget:
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        refresh_btn = Gtk.Button(label='Refresh Schedule')
        refresh_btn.get_style_context().add_class('salat-btn')
        refresh_btn.connect('clicked', lambda *_: self.on_refresh_schedule())

        reset_pos_btn = Gtk.Button(label='Reset Pill Position')
        reset_pos_btn.get_style_context().add_class('salat-btn')
        reset_pos_btn.connect('clicked', lambda *_: self.on_reset_position())

        box.pack_start(refresh_btn, True, True, 0)
        box.pack_start(reset_pos_btn, True, True, 0)
        return box

    def _sync_from_config(self) -> None:
        cfg = self.config_service.config
        for key, spin in self._spin_buttons.items():
            spin.set_value(cfg.iqama_delays.get(key, DEFAULT_IQAMA_DELAYS[key]))
        self.notif_switch.set_active(cfg.notifications_enabled)
        self.jumaa_switch.set_active(cfg.friday_reminder_enabled)
        self.jumaa_spin.set_value(cfg.friday_reminder_minutes)
        self.jumaa_spin.set_sensitive(cfg.friday_reminder_enabled)
        self.audio_switch.set_active(cfg.audio_enabled)
        self.lock_switch.set_active(cfg.lock_enabled)
        self.lock_entry.set_text(cfg.custom_lock_command or 'ft_lock')
        self.overlay_switch.set_active(cfg.overlay_mode)
        self._draft_audio_path = cfg.adhan_audio_path or ''
        self._update_audio_label()

    def _update_audio_label(self) -> None:
        custom = self._draft_audio_path.strip()
        if custom:
            self.audio_path_lbl.set_text(os.path.basename(custom))
            self.audio_path_lbl.set_tooltip_text(custom)
        else:
            self.audio_path_lbl.set_text('Default (assets/adan.mp3)')
            self.audio_path_lbl.set_tooltip_text('')

    def _on_reset_iqama(self, _btn: Gtk.Button) -> None:
        for key, spin in self._spin_buttons.items():
            spin.set_value(DEFAULT_IQAMA_DELAYS[key])

    def _on_choose_audio(self, _btn: Gtk.Button) -> None:
        dialog = Gtk.FileChooserDialog(
            title='Select Adhan Audio File',
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
        audio_filter.set_name('Audio files (MP3, WAV, OGG, FLAC, M4A)')
        for pattern in ('*.mp3', '*.wav', '*.ogg', '*.flac', '*.m4a', '*.aac'):
            audio_filter.add_pattern(pattern)
        dialog.add_filter(audio_filter)

        if dialog.run() == Gtk.ResponseType.OK:
            self._draft_audio_path = dialog.get_filename() or ''
            self._update_audio_label()
        dialog.destroy()

    def _on_clear_audio(self, _btn: Gtk.Button) -> None:
        self._draft_audio_path = ''
        self._update_audio_label()

    def _on_test_audio(self, _btn: Gtk.Button) -> None:
        if self.audio_service.is_playing:
            self.audio_service.stop()
            self.test_audio_btn.set_label('Test Audio')
        else:
            ok = self.audio_service.play(self._draft_audio_path)
            if ok:
                self.test_audio_btn.set_label('Stop Audio')

    def _on_save_clicked(self, _btn: Gtk.Button) -> None:
        cfg = self.config_service.config
        prev_overlay = cfg.overlay_mode

        for key, spin in self._spin_buttons.items():
            cfg.iqama_delays[key] = int(spin.get_value())

        cfg.notifications_enabled = self.notif_switch.get_active()
        cfg.friday_reminder_enabled = self.jumaa_switch.get_active()
        cfg.friday_reminder_minutes = int(self.jumaa_spin.get_value())
        cfg.audio_enabled = self.audio_switch.get_active()
        cfg.adhan_audio_path = self._draft_audio_path
        cfg.lock_enabled = self.lock_switch.get_active()
        cfg.custom_lock_command = self.lock_entry.get_text().strip() or 'ft_lock'
        cfg.overlay_mode = self.overlay_switch.get_active()

        overlay_changed = cfg.overlay_mode != prev_overlay
        self.audio_service.stop()
        self.test_audio_btn.set_label('Test Audio')
        self.hide()

        self.config_service.save(notify=not overlay_changed)
        if overlay_changed:
            self.on_overlay_changed(cfg.overlay_mode)

    def _on_key_press(self, _widget, event) -> bool:
        if event.keyval == Gdk.KEY_Escape:
            self._cancel_and_close()
            return True
        return False

    def _on_delete(self, _widget, _event) -> bool:
        self._cancel_and_close()
        return True

    def _cancel_and_close(self) -> None:
        self.audio_service.stop()
        self.test_audio_btn.set_label('Test Audio')
        self.hide()

    def open_window(self) -> None:
        self._sync_from_config()
        self.show_all()
        self.present()
