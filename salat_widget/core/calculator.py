"""Pure prayer time & Iqama countdown calculation utilities."""

import datetime
from typing import Dict, List, Optional

from salat_widget.constants import DEFAULT_IQAMA_DELAYS, PRAYER_LABELS, PRAYER_ORDER
from salat_widget.models import ActivePrayer, PrayerEntry


def format_countdown(total_seconds: float) -> str:
    seconds = max(0, int(total_seconds))
    hours, rem = divmod(seconds, 3600)
    minutes, secs = divmod(rem, 60)
    if hours > 0:
        return f'{hours:02d}:{minutes:02d}:{secs:02d}'
    return f'{minutes:02d}:{secs:02d}'


def parse_prayer_entries(
    day_data: Optional[Dict[str, str]],
    iqama_delays: Dict[str, int],
    now: datetime.datetime,
) -> List[PrayerEntry]:
    if not day_data:
        return []

    entries: List[PrayerEntry] = []
    is_friday = now.weekday() == 4
    for key in PRAYER_ORDER:
        raw_time = day_data.get(key)
        if not raw_time or ':' not in raw_time:
            continue
        parts = raw_time.split(':')
        hour, minute = int(parts[0]), int(parts[1])
        adhan_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        delay = int(iqama_delays.get(key, DEFAULT_IQAMA_DELAYS[key]))
        iqama_dt = adhan_dt + datetime.timedelta(minutes=delay)
        display_name = "Jumu'ah" if (key == 'Dhuhr' and is_friday) else PRAYER_LABELS[key]
        entries.append(
            PrayerEntry(
                key=key,
                name=display_name,
                time_str=f'{hour:02d}:{minute:02d}',
                delay_minutes=delay,
                adhan_dt=adhan_dt,
                iqama_dt=iqama_dt,
            )
        )
    return entries


def find_active_prayer(
    entries: List[PrayerEntry],
    iqama_delays: Dict[str, int],
    now: datetime.datetime,
) -> Optional[ActivePrayer]:
    if not entries:
        return None

    for entry in entries:
        if entry.adhan_dt <= now < entry.iqama_dt:
            return ActivePrayer(phase='IQAMA', prayer=entry)

    for entry in entries:
        if entry.adhan_dt > now:
            return ActivePrayer(phase='NEXT_ADHAN', prayer=entry)

    # Past Isha -> next is tomorrow's Fajr
    fajr = entries[0]
    tomorrow_adhan = fajr.adhan_dt + datetime.timedelta(days=1)
    fajr_delay = int(iqama_delays.get('Fajr', DEFAULT_IQAMA_DELAYS['Fajr']))
    tomorrow_iqama = tomorrow_adhan + datetime.timedelta(minutes=fajr_delay)
    next_fajr = PrayerEntry(
        key=fajr.key,
        name=fajr.name,
        time_str=fajr.time_str,
        delay_minutes=fajr_delay,
        adhan_dt=tomorrow_adhan,
        iqama_dt=tomorrow_iqama,
    )
    return ActivePrayer(phase='NEXT_ADHAN', prayer=next_fajr)


def calculate_progress(
    active: ActivePrayer,
    entries: List[PrayerEntry],
    now: datetime.datetime,
) -> float:
    try:
        if active.phase == 'IQAMA':
            start = active.prayer.adhan_dt
            end = active.prayer.iqama_dt
        else:
            idx = next((i for i, e in enumerate(entries) if e.key == active.prayer.key), 0)
            if idx > 0:
                start = entries[idx - 1].iqama_dt
            else:
                start = active.prayer.adhan_dt - datetime.timedelta(hours=8)
            end = active.prayer.adhan_dt

        total = max(1.0, (end - start).total_seconds())
        elapsed = max(0.0, (now - start).total_seconds())
        return min(1.0, max(0.04, elapsed / total))
    except Exception:
        return 0.3


def check_jumaa_reminder(
    entries: List[PrayerEntry],
    now: datetime.datetime,
    reminder_minutes: int,
) -> Optional[int]:
    """Return remaining minutes until Jumu'ah if within reminder window on Friday, else None."""
    if now.weekday() != 4:
        return None
    dhuhr = next((e for e in entries if e.key == 'Dhuhr'), None)
    if not dhuhr:
        return None
    diff_seconds = (dhuhr.adhan_dt - now).total_seconds()
    if 0 < diff_seconds <= (reminder_minutes * 60):
        return max(1, int((diff_seconds + 59) // 60))
    return None
