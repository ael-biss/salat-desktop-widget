"""Application constants, paths, and Sala Al Jadida defaults."""

import os

APP_NAME = 'Salat Desktop Widget'
CITY_NAME = 'Sala Al Jadida'
API_MONTH_URL = 'https://small-morning-6206.abdo-bissari.workers.dev/api/sala-al-jadida/month.json'

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(PACKAGE_DIR)
ASSETS_DIR = os.path.join(REPO_DIR, 'assets')
DEFAULT_ICON_PATH = os.path.join(ASSETS_DIR, 'mosque.svg')
RED_ICON_PATH = os.path.join(ASSETS_DIR, 'mosque_red.svg')
DEFAULT_ADHAN_PATH = os.path.join(ASSETS_DIR, 'adan.mp3')

CONFIG_DIR = os.path.expanduser('~/.config/salat-widget')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
CACHE_FILE = os.path.join(CONFIG_DIR, 'cache.json')

PRAYER_ORDER = ('Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Ishae')
DISPLAY_ORDER = ('Fajr', 'Chourouq', 'Dhuhr', 'Asr', 'Maghrib', 'Ishae')

PRAYER_LABELS = {
    'Fajr': 'Fajr',
    'Chourouq': 'Chourouq',
    'Dhuhr': 'Dhuhr',
    'Asr': 'Asr',
    'Maghrib': 'Maghrib',
    'Ishae': 'Isha',
}

DEFAULT_IQAMA_DELAYS = {
    'Fajr': 25,
    'Dhuhr': 12,
    'Asr': 12,
    'Maghrib': 7,
    'Ishae': 12,
}

DEFAULT_FRIDAY_REMINDER_MINUTES = 60
CACHE_TTL_SECONDS = 12 * 3600  # 12 hours
