"""Application constants, paths, and Sala Al Jadida defaults."""

import os
import zipfile

APP_NAME = 'Salat Desktop Widget'
CITY_NAME = 'Sala Al Jadida'
API_MONTH_URL = 'https://small-morning-6206.abdo-bissari.workers.dev/api/sala-al-jadida/month.json'

# GitHub Releases API endpoint for automatic update checks
UPDATE_MANIFEST_URL = os.environ.get(
    'SALAT_UPDATE_URL',
    'https://api.github.com/repos/ael-biss/salat-desktop-widget/releases/latest',
)

PACKAGE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(PACKAGE_DIR)

DATA_DIR = os.path.expanduser('~/.local/share/salat-widget')
INSTALL_BIN_PATH = os.path.expanduser('~/.local/bin/salat-widget')
CONFIG_DIR = os.path.expanduser('~/.config/salat-widget')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'config.json')
CACHE_FILE = os.path.join(CONFIG_DIR, 'cache.json')


def _resolve_assets_dir() -> str:
    """Use repo assets/ in dev mode, or extract bundled assets from .pyz into ~/.local/share/salat-widget/assets."""
    local_assets = os.path.join(REPO_DIR, 'assets')
    if os.path.isdir(local_assets) and os.path.exists(os.path.join(local_assets, 'mosque.svg')):
        return local_assets

    extracted_dir = os.path.join(DATA_DIR, 'assets')
    os.makedirs(extracted_dir, exist_ok=True)

    # When running from a single-file .pyz bundle, REPO_DIR is the .pyz archive path
    if os.path.isfile(REPO_DIR) and zipfile.is_zipfile(REPO_DIR):
        with zipfile.ZipFile(REPO_DIR, 'r') as zf:
            for name in zf.namelist():
                if name.startswith('assets/') and not name.endswith('/'):
                    rel = os.path.basename(name)
                    target = os.path.join(extracted_dir, rel)
                    if not os.path.exists(target):
                        with zf.open(name) as src, open(target, 'wb') as dst:
                            dst.write(src.read())
    return extracted_dir


ASSETS_DIR = _resolve_assets_dir()
DEFAULT_ICON_PATH = os.path.join(ASSETS_DIR, 'mosque.svg')
RED_ICON_PATH = os.path.join(ASSETS_DIR, 'mosque_red.svg')
DEFAULT_ADHAN_PATH = os.path.join(ASSETS_DIR, 'adan.mp3')

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
