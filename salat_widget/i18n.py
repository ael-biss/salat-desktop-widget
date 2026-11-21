"""English & Arabic localization strings and date/prayer formatting helpers."""

import datetime
from typing import Dict

SUPPORTED_LANGUAGES = ('en', 'ar')

PRAYER_NAMES: Dict[str, Dict[str, str]] = {
    'en': {
        'Fajr': 'Fajr',
        'Chourouq': 'Chourouq',
        'Dhuhr': 'Dhuhr',
        'Jumaa': "Jumu'ah",
        'Asr': 'Asr',
        'Maghrib': 'Maghrib',
        'Ishae': 'Isha',
    },
    'ar': {
        'Fajr': 'الفجر',
        'Chourouq': 'الشروق',
        'Dhuhr': 'الظهر',
        'Jumaa': 'الجمعة',
        'Asr': 'العصر',
        'Maghrib': 'المغرب',
        'Ishae': 'العشاء',
    },
}

AR_WEEKDAYS = (
    'الإثنين',
    'الثلاثاء',
    'الأربعاء',
    'الخميس',
    'الجمعة',
    'السبت',
    'الأحد',
)

AR_MONTHS = (
    'يناير',
    'فبراير',
    'مارس',
    'أبريل',
    'مايو',
    'يونيو',
    'يوليو',
    'أغسطس',
    'سبتمبر',
    'أكتوبر',
    'نوفمبر',
    'ديسمبر',
)

STRINGS: Dict[str, Dict[str, str]] = {
    'en': {
        'app_name': 'Salat Desktop Widget',
        'city_name': 'Sala Al Jadida',
        'salat': 'Salat',
        'syncing': 'Sync...',
        'offline': 'Offline',
        'iqama_prefix': 'Iqama {prayer}',
        'next_prayer': 'NEXT PRAYER',
        'iqama_countdown': 'IQAMA COUNTDOWN',
        'loading_schedule': 'Loading Sala Al Jadida schedule...',
        'view_monthly_schedule': 'View Full Monthly Schedule',
        'settings': 'Settings',
        'refresh': 'Refresh',
        'reload_app': 'Reload App',
        'quit': 'Quit',
        'quit_app': 'Quit App',
        'close': 'Close',
        'cancel': 'Cancel',
        'save': 'Save',
        'min_short': 'min',
        'iqama_pill': '+{minutes}m',
        # Settings window
        'settings_win_title': 'Salat Widget Settings',
        'widget_settings': 'Widget Settings',
        'settings_subtitle': 'City: {city} • Click Save to apply changes',
        'sec_language': 'LANGUAGE',
        'language_label': 'Interface Language',
        'sec_top_bar': 'TOP BAR & POSITION',
        'dock_top_bar': 'Dock in GNOME Top Bar (X11)',
        'top_bar_hint': 'Auto-hides on fullscreen & lock screen. Middle-drag or use presets below to move cleanly.',
        'preset_left': 'Left of Clock',
        'preset_right': 'Right of Clock',
        'preset_far_right': 'Far Right',
        'sec_iqama': 'IQAMA DELAYS (MINUTES)',
        'reset_defaults': 'Reset Defaults',
        'sec_jumaa': "JUMU'AH (FRIDAY) REMINDER",
        'jumaa_toggle': "Remind before Jumu'ah prayer",
        'minutes_before_adhan': 'Minutes before Adhan',
        'sec_audio': 'AUDIO & NOTIFICATIONS',
        'desktop_notifications': 'Desktop Notifications',
        'play_adhan_audio': 'Play Adhan Audio',
        'custom_adhan_file': 'Custom Adhan File (optional)',
        'default_audio_label': 'Default (assets/adan.mp3)',
        'choose_file': 'Choose File...',
        'use_default': 'Use Default',
        'test_audio': 'Test Audio',
        'stop_audio': 'Stop Audio',
        'select_audio_title': 'Select Adhan Audio File',
        'audio_filter_name': 'Audio files (MP3, WAV, OGG, FLAC, M4A)',
        'sec_lock': 'AUTO-LOCK ON IQAMA',
        'lock_toggle': 'Lock screen when Iqama starts',
        'lock_command': 'Lock Command',
        'refresh_schedule': 'Refresh Schedule',
        'reset_position': 'Reset Pill Position',
        'version_label': 'Version v{version}',
        'check_updates': 'Check for Updates',
        'checking_updates': 'Checking for updates...',
        'downloading_update': 'Downloading update...',
        'update_available_lbl': 'Update available: {version}',
        'install_version': 'Install {version}',
        'up_to_date': 'v{version} • Up to date',
        'updated_restarting': 'Updated! Restarting...',
        'update_failed': 'Update failed: {msg}',
        # Monthly schedule window
        'monthly_win_title': 'Monthly Prayer Schedule — {city}',
        'monthly_header_default': '{city} — Monthly Schedule',
        'loading_monthly': 'Loading schedule...',
        'could_not_load': 'Could not load schedule: {msg}',
        'no_schedule_data': 'No schedule data available. Click Refresh to fetch.',
        'days_count': '{count} days',
        'col_day': 'Day',
        'col_hijri': 'Hijri',
        'col_date': 'Date',
        'col_fajr': 'Fajr',
        'col_sunrise': 'Sunrise',
        'col_dhuhr': 'Dhuhr',
        'col_asr': 'Asr',
        'col_maghrib': 'Maghrib',
        'col_isha': 'Isha',
        # Notifications
        'notif_update_title': 'Salat Widget Update Available',
        'notif_update_body': 'Version {version} is available. Open Settings to update.',
        'notif_jumaa_title': "Jumu'ah Reminder",
        'notif_jumaa_body': "Jumu'ah prayer is in {minutes} minutes. Prepare for Friday prayer.",
        'notif_adhan_title': '{prayer} Adhan',
        'notif_adhan_body': 'It is time for {prayer} prayer in Sala Al Jadida.',
        'notif_iqama_title': '{prayer} Iqama',
        'notif_iqama_body': 'Congregation prayer is starting now.',
    },
    'ar': {
        'app_name': 'مواقيت الصلاة',
        'city_name': 'سلا الجديدة',
        'salat': 'الصلاة',
        'syncing': 'مزامنة...',
        'offline': 'غير متصل',
        'iqama_prefix': 'إقامة {prayer}',
        'next_prayer': 'الصلاة القادمة',
        'iqama_countdown': 'العد التنازلي للإقامة',
        'loading_schedule': 'جاري تحميل مواقيت سلا الجديدة...',
        'view_monthly_schedule': 'عرض جدول الشهر الكامل',
        'settings': 'الإعدادات',
        'refresh': 'تحديث',
        'reload_app': 'إعادة التشغيل',
        'quit': 'خروج',
        'quit_app': 'إغلاق التطبيق',
        'close': 'إغلاق',
        'cancel': 'إلغاء',
        'save': 'حفظ',
        'min_short': 'د',
        'iqama_pill': '+{minutes}د',
        # Settings window
        'settings_win_title': 'إعدادات مواقيت الصلاة',
        'widget_settings': 'إعدادات التطبيق',
        'settings_subtitle': 'المدينة: {city} • اضغط حفظ لتطبيق التغييرات',
        'sec_language': 'اللغة',
        'language_label': 'لغة الواجهة',
        'sec_top_bar': 'الشريط العلوي والموقع',
        'dock_top_bar': 'تثبيت في الشريط العلوي (X11)',
        'top_bar_hint': 'يختفي تلقائياً عند ملء الشاشة أو القفل. اسحب أو استخدم المواقع السريعة بالأسفل.',
        'preset_left': 'يسار الساعة',
        'preset_right': 'يمين الساعة',
        'preset_far_right': 'أقصى اليمين',
        'sec_iqama': 'مدة الإقامة (بالدقائق)',
        'reset_defaults': 'استعادة الافتراضي',
        'sec_jumaa': 'تذكير صلاة الجمعة',
        'jumaa_toggle': 'التذكير قبل صلاة الجمعة',
        'minutes_before_adhan': 'عدد الدقائق قبل الأذان',
        'sec_audio': 'الصوت والإشعارات',
        'desktop_notifications': 'إشعارات سطح المكتب',
        'play_adhan_audio': 'تشغيل صوت الأذان',
        'custom_adhan_file': 'ملف أذان مخصص (اختياري)',
        'default_audio_label': 'الافتراضي (assets/adan.mp3)',
        'choose_file': 'اختيار ملف...',
        'use_default': 'الافتراضي',
        'test_audio': 'تجربة الصوت',
        'stop_audio': 'إيقاف الصوت',
        'select_audio_title': 'اختر ملف صوت الأذان',
        'audio_filter_name': 'ملفات صوتية (MP3, WAV, OGG, FLAC, M4A)',
        'sec_lock': 'القفل التلقائي عند الإقامة',
        'lock_toggle': 'قفل الشاشة عند بداية الإقامة',
        'lock_command': 'أمر القفل',
        'refresh_schedule': 'تحديث المواقيت',
        'reset_position': 'إعادة ضبط الموقع',
        'version_label': 'الإصدار v{version}',
        'check_updates': 'التحقق من التحديثات',
        'checking_updates': 'جاري التحقق من التحديثات...',
        'downloading_update': 'جاري تحميل التحديث...',
        'update_available_lbl': 'تحديث متوفر: {version}',
        'install_version': 'تثبيت {version}',
        'up_to_date': 'v{version} • محدث لآخر إصدار',
        'updated_restarting': 'تم التحديث! جاري إعادة التشغيل...',
        'update_failed': 'فشل التحديث: {msg}',
        # Monthly schedule window
        'monthly_win_title': 'جدول مواقيت الشهر — {city}',
        'monthly_header_default': '{city} — جدول الشهر',
        'loading_monthly': 'جاري تحميل الجدول...',
        'could_not_load': 'تعذر تحميل الجدول: {msg}',
        'no_schedule_data': 'لا توجد بيانات متاحة. اضغط تحديث للجلب.',
        'days_count': '{count} يوم',
        'col_day': 'اليوم',
        'col_hijri': 'هجري',
        'col_date': 'التاريخ',
        'col_fajr': 'الفجر',
        'col_sunrise': 'الشروق',
        'col_dhuhr': 'الظهر',
        'col_asr': 'العصر',
        'col_maghrib': 'المغرب',
        'col_isha': 'العشاء',
        # Notifications
        'notif_update_title': 'تحديث جديد متوفر لمواقيت الصلاة',
        'notif_update_body': 'الإصدار {version} متوفر الآن. افتح الإعدادات للتحديث.',
        'notif_jumaa_title': 'تذكير صلاة الجمعة',
        'notif_jumaa_body': 'تبقى {minutes} دقيقة على صلاة الجمعة. استعد للصلاة.',
        'notif_adhan_title': 'أذان {prayer}',
        'notif_adhan_body': 'حان الآن وقت صلاة {prayer} في سلا الجديدة.',
        'notif_iqama_title': 'إقامة {prayer}',
        'notif_iqama_body': 'تقام الآن صلاة {prayer} جماعة.',
    },
}


def normalize_lang(lang: str) -> str:
    return 'ar' if str(lang or '').strip().lower() == 'ar' else 'en'


def is_rtl(lang: str) -> bool:
    return normalize_lang(lang) == 'ar'


def tr(lang: str, key: str, **kwargs) -> str:
    norm = normalize_lang(lang)
    table = STRINGS.get(norm, STRINGS['en'])
    template = table.get(key) or STRINGS['en'].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template


def prayer_name(key: str, lang: str = 'en', is_friday: bool = False) -> str:
    norm = normalize_lang(lang)
    lookup_key = 'Jumaa' if (key == 'Dhuhr' and is_friday) else key
    return PRAYER_NAMES[norm].get(lookup_key, PRAYER_NAMES['en'].get(lookup_key, key))


def format_date(dt: datetime.datetime, lang: str = 'en') -> str:
    if normalize_lang(lang) == 'ar':
        day_name = AR_WEEKDAYS[dt.weekday()]
        month_name = AR_MONTHS[dt.month - 1]
        return f'{day_name}، {dt.day} {month_name} {dt.year}'
    return dt.strftime('%A, %d %b %Y')
