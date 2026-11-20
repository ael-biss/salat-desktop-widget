"""Prayer schedule fetching and caching for Sala Al Jadida."""

import datetime
import json
import os
import threading
import time
import urllib.request
from typing import Callable, Dict, Optional

from salat_widget.constants import API_MONTH_URL, CACHE_FILE, CACHE_TTL_SECONDS, CONFIG_DIR


class PrayerService:
    def __init__(self) -> None:
        self._cache: dict = self._load_cache()

    def get_today_cached(self, today: datetime.date) -> Optional[Dict[str, str]]:
        days_map = self._cache.get('days', {})
        entry = days_map.get(today.isoformat())
        if isinstance(entry, dict) and entry.get('Fajr'):
            return entry
        return None

    def is_cache_stale(self) -> bool:
        last_sync = float(self._cache.get('last_sync', 0))
        return (time.time() - last_sync) >= CACHE_TTL_SECONDS

    def fetch_async(
        self,
        today: datetime.date,
        force: bool,
        on_success: Callable[[Dict[str, str]], None],
        on_error: Callable[[str], None],
    ) -> None:
        if not force:
            cached = self.get_today_cached(today)
            if cached and not self.is_cache_stale():
                on_success(cached)
                return

        def worker() -> None:
            try:
                data = self._fetch_month_sync(today)
                if data:
                    on_success(data)
                else:
                    fallback = self.get_today_cached(today)
                    if fallback:
                        on_success(fallback)
                    else:
                        on_error('No prayer data found for today.')
            except Exception as exc:
                fallback = self.get_today_cached(today)
                if fallback:
                    on_success(fallback)
                else:
                    on_error(str(exc))

        threading.Thread(target=worker, daemon=True).start()

    def _fetch_month_sync(self, today: datetime.date) -> Optional[Dict[str, str]]:
        req = urllib.request.Request(
            API_MONTH_URL,
            headers={'User-Agent': 'SalatDesktopWidget/1.0'},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            parsed = json.loads(resp.read().decode('utf-8'))

        raw_days = parsed.get('days') if isinstance(parsed, dict) else None
        if not isinstance(raw_days, list) or not raw_days:
            return None

        days_map: Dict[str, Dict[str, str]] = self._cache.get('days', {})
        for day in raw_days:
            iso = day.get('date')
            if not iso:
                continue
            days_map[iso] = {
                'Fajr': day.get('fajr', ''),
                'Chourouq': day.get('sunrise', ''),
                'Dhuhr': day.get('dhuhr', ''),
                'Asr': day.get('asr', ''),
                'Maghrib': day.get('maghrib', ''),
                'Ishae': day.get('isha', ''),
                'date': iso,
            }

        self._cache['days'] = days_map
        self._cache['last_sync'] = time.time()
        self._save_cache()
        return days_map.get(today.isoformat())

    def _load_cache(self) -> dict:
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    return data
            except Exception:
                pass
        return {'days': {}, 'last_sync': 0}

    def _save_cache(self) -> None:
        try:
            os.makedirs(CONFIG_DIR, mode=0o700, exist_ok=True)
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._cache, f, indent=2, ensure_ascii=False)
            os.chmod(CACHE_FILE, 0o600)
        except Exception:
            pass
