"""Automated tests for Salat Desktop Widget (Adhan, Iqama red state, Jumu'ah, Config)."""

import ctypes
import datetime
import os
import unittest

from salat_widget.constants import DEFAULT_ADHAN_PATH, DEFAULT_ICON_PATH, RED_ICON_PATH
from salat_widget.core.calculator import (
    calculate_progress,
    check_jumaa_reminder,
    find_active_prayer,
    format_countdown,
    parse_prayer_entries,
)
from salat_widget.i18n import STRINGS, format_date, is_rtl, normalize_lang, prayer_name, tr
from salat_widget.models import UserConfig
from salat_widget.services.update_service import is_newer_version, parse_semver
from salat_widget.services.x11_topbar import (
    XI_RAW_BUTTON_PRESS,
    XI_RAW_BUTTON_RELEASE,
    XI_RAW_MOTION,
    XEvent,
    XGenericEventCookie,
    XIRawEvent,
    set_xi_mask,
)

SAMPLE_DAY = {
    'Fajr': '05:08',
    'Chourouq': '06:34',
    'Dhuhr': '12:17',
    'Asr': '15:22',
    'Maghrib': '17:51',
    'Ishae': '19:06',
}


class TestSalatWidget(unittest.TestCase):
    def test_assets_exist(self):
        self.assertTrue(os.path.exists(DEFAULT_ICON_PATH), 'mosque.svg missing')
        self.assertTrue(os.path.exists(RED_ICON_PATH), 'mosque_red.svg missing')
        self.assertTrue(os.path.exists(DEFAULT_ADHAN_PATH), 'adan.mp3 missing')

    def test_red_icon_contains_red_palette(self):
        with open(RED_ICON_PATH, 'r', encoding='utf-8') as f:
            svg = f.read()
        self.assertIn('#dc2626', svg)
        self.assertNotIn('#047857', svg)

    def test_adhan_and_iqama_phase_transitions(self):
        cfg = UserConfig()
        # 2 minutes before Dhuhr Adhan (Thursday 2026-11-19)
        before_adhan = datetime.datetime(2026, 11, 19, 12, 15, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, before_adhan)
        active = find_active_prayer(entries, cfg.iqama_delays, before_adhan)
        self.assertIsNotNone(active)
        self.assertEqual(active.phase, 'NEXT_ADHAN')
        self.assertEqual(active.prayer.key, 'Dhuhr')
        self.assertEqual(active.prayer.name, 'Dhuhr')
        self.assertEqual(format_countdown((active.prayer.adhan_dt - before_adhan).total_seconds()), '02:00')

        # Exactly at Dhuhr Adhan -> enters IQAMA phase (red icon mode)
        at_adhan = datetime.datetime(2026, 11, 19, 12, 17, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, at_adhan)
        active = find_active_prayer(entries, cfg.iqama_delays, at_adhan)
        self.assertEqual(active.phase, 'IQAMA')
        self.assertEqual(active.prayer.key, 'Dhuhr')
        self.assertEqual(format_countdown((active.prayer.iqama_dt - at_adhan).total_seconds()), '12:00')

        # 5 minutes into Iqama -> still IQAMA, 7 minutes left
        mid_iqama = datetime.datetime(2026, 11, 19, 12, 22, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, mid_iqama)
        active = find_active_prayer(entries, cfg.iqama_delays, mid_iqama)
        self.assertEqual(active.phase, 'IQAMA')
        self.assertEqual(format_countdown((active.prayer.iqama_dt - mid_iqama).total_seconds()), '07:00')
        progress = calculate_progress(active, entries, mid_iqama)
        self.assertAlmostEqual(progress, 5.0 / 12.0, places=2)

        # At Iqama end (12:29:00) -> back to NEXT_ADHAN (Asr)
        after_iqama = datetime.datetime(2026, 11, 19, 12, 29, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, after_iqama)
        active = find_active_prayer(entries, cfg.iqama_delays, after_iqama)
        self.assertEqual(active.phase, 'NEXT_ADHAN')
        self.assertEqual(active.prayer.key, 'Asr')

    def test_custom_iqama_delay_modifies_countdown(self):
        cfg = UserConfig.from_dict({'iqamaDelays': {'Maghrib': 15}})
        self.assertEqual(cfg.iqama_delays['Maghrib'], 15)
        now = datetime.datetime(2026, 11, 19, 17, 56, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, now)
        active = find_active_prayer(entries, cfg.iqama_delays, now)
        self.assertEqual(active.phase, 'IQAMA')
        self.assertEqual(active.prayer.key, 'Maghrib')
        self.assertEqual(format_countdown((active.prayer.iqama_dt - now).total_seconds()), '10:00')

    def test_jumaa_reminder_friday_only(self):
        cfg = UserConfig(friday_reminder_enabled=True, friday_reminder_minutes=60)
        # Friday 2026-11-20, 45 minutes before Dhuhr (12:17) -> 11:32
        friday_in_window = datetime.datetime(2026, 11, 20, 11, 32, 0)
        entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, friday_in_window)
        dhuhr = next(e for e in entries if e.key == 'Dhuhr')
        self.assertEqual(dhuhr.name, "Jumu'ah")
        rem = check_jumaa_reminder(entries, friday_in_window, cfg.friday_reminder_minutes)
        self.assertEqual(rem, 45)

        # Friday 2 hours before Dhuhr -> outside 60m window
        friday_early = datetime.datetime(2026, 11, 20, 10, 0, 0)
        self.assertIsNone(check_jumaa_reminder(entries, friday_early, cfg.friday_reminder_minutes))

        # Thursday 45 minutes before Dhuhr -> NOT Friday
        thursday = datetime.datetime(2026, 11, 19, 11, 32, 0)
        thurs_entries = parse_prayer_entries(SAMPLE_DAY, cfg.iqama_delays, thursday)
        self.assertIsNone(check_jumaa_reminder(thurs_entries, thursday, cfg.friday_reminder_minutes))

    def test_config_roundtrip_with_friday_settings(self):
        cfg = UserConfig(
            friday_reminder_enabled=False,
            friday_reminder_minutes=45,
            lock_enabled=True,
            custom_lock_command='ft_lock',
        )
        restored = UserConfig.from_dict(cfg.to_dict())
        self.assertFalse(restored.friday_reminder_enabled)
        self.assertEqual(restored.friday_reminder_minutes, 45)
        self.assertTrue(restored.lock_enabled)
        self.assertEqual(restored.custom_lock_command, 'ft_lock')

    def test_update_semver_comparison(self):
        self.assertEqual(parse_semver('v1.2.3'), (1, 2, 3))
        self.assertTrue(is_newer_version('v1.0.1', '1.0.0'))
        self.assertTrue(is_newer_version('2.0.0', '1.9.9'))
        self.assertFalse(is_newer_version('1.0.0', '1.0.0'))
        self.assertFalse(is_newer_version('0.9.9', '1.0.0'))

    def test_config_roundtrip_top_bar_settings(self):
        # Old config without topBarMode defaults cleanly to Top Bar Mode
        legacy = UserConfig.from_dict({'widgetX': 12, 'widgetY': 32})
        self.assertTrue(legacy.top_bar_mode)
        self.assertIsNone(legacy.top_bar_x)
        self.assertFalse(legacy.position_locked)

        cfg = UserConfig(top_bar_mode=False, top_bar_x=1180, position_locked=True)
        restored = UserConfig.from_dict(cfg.to_dict())
        self.assertFalse(restored.top_bar_mode)
        self.assertEqual(restored.top_bar_x, 1180)
        self.assertTrue(restored.position_locked)

    def test_x11_topbar_xi_mask_and_structs(self):
        buf = (ctypes.c_ubyte * 4)()
        set_xi_mask(buf, XI_RAW_BUTTON_PRESS)
        set_xi_mask(buf, XI_RAW_BUTTON_RELEASE)
        set_xi_mask(buf, XI_RAW_MOTION)
        self.assertEqual(buf[0], 0x00)
        self.assertEqual(buf[1], 0x80)  # bit 15
        self.assertEqual(buf[2], 0x03)  # bits 16 & 17
        self.assertEqual(buf[3], 0x00)
        self.assertGreaterEqual(ctypes.sizeof(XEvent), 192)
        self.assertGreater(ctypes.sizeof(XGenericEventCookie), 0)
        self.assertGreater(ctypes.sizeof(XIRawEvent), 0)

    def test_arabic_and_english_i18n(self):
        # All English keys have Arabic translations
        self.assertEqual(set(STRINGS['en'].keys()), set(STRINGS['ar'].keys()))
        self.assertEqual(normalize_lang('ar'), 'ar')
        self.assertEqual(normalize_lang('AR'), 'ar')
        self.assertEqual(normalize_lang('unknown'), 'en')
        self.assertTrue(is_rtl('ar'))
        self.assertFalse(is_rtl('en'))

        self.assertEqual(prayer_name('Dhuhr', lang='ar', is_friday=False), 'الظهر')
        self.assertEqual(prayer_name('Dhuhr', lang='ar', is_friday=True), 'الجمعة')
        self.assertEqual(prayer_name('Ishae', lang='ar'), 'العشاء')
        self.assertEqual(tr('ar', 'iqama_prefix', prayer='المغرب'), 'إقامة المغرب')

        sat = datetime.datetime(2026, 11, 21, 11, 0, 0)
        self.assertEqual(format_date(sat, 'ar'), 'السبت، 21 نوفمبر 2026')

        entries_ar = parse_prayer_entries(SAMPLE_DAY, UserConfig().iqama_delays, sat, lang='ar')
        self.assertEqual(entries_ar[0].name, 'الفجر')

        cfg = UserConfig(language='ar')
        restored = UserConfig.from_dict(cfg.to_dict())
        self.assertEqual(restored.language, 'ar')


if __name__ == '__main__':
    unittest.main()
