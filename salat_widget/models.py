"""Data models for configuration and prayer schedules."""

from dataclasses import dataclass, field
import datetime
from typing import Dict, Optional

from salat_widget.constants import DEFAULT_FRIDAY_REMINDER_MINUTES, DEFAULT_IQAMA_DELAYS
from salat_widget.i18n import normalize_lang


@dataclass
class UserConfig:
    iqama_delays: Dict[str, int] = field(default_factory=lambda: dict(DEFAULT_IQAMA_DELAYS))
    audio_enabled: bool = True
    adhan_audio_path: str = ''
    notifications_enabled: bool = True
    friday_reminder_enabled: bool = True
    friday_reminder_minutes: int = DEFAULT_FRIDAY_REMINDER_MINUTES
    lock_enabled: bool = False
    custom_lock_command: str = 'ft_lock'
    widget_x: Optional[int] = None
    widget_y: Optional[int] = None
    top_bar_mode: bool = True
    top_bar_x: Optional[int] = None
    position_locked: bool = False
    language: str = 'en'

    def to_dict(self) -> dict:
        return {
            'iqamaDelays': dict(self.iqama_delays),
            'audioEnabled': self.audio_enabled,
            'adhanAudioPath': self.adhan_audio_path,
            'notificationsEnabled': self.notifications_enabled,
            'fridayReminderEnabled': self.friday_reminder_enabled,
            'fridayReminderMinutes': self.friday_reminder_minutes,
            'lockEnabled': self.lock_enabled,
            'customLockCommand': self.custom_lock_command,
            'widgetX': self.widget_x,
            'widgetY': self.widget_y,
            'topBarMode': self.top_bar_mode,
            'topBarX': self.top_bar_x,
            'positionLocked': self.position_locked,
            'language': normalize_lang(self.language),
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'UserConfig':
        delays = dict(DEFAULT_IQAMA_DELAYS)
        raw_delays = data.get('iqamaDelays')
        if isinstance(raw_delays, dict):
            for key in DEFAULT_IQAMA_DELAYS:
                try:
                    val = int(raw_delays.get(key, delays[key]))
                    if 1 <= val <= 120:
                        delays[key] = val
                except (TypeError, ValueError):
                    pass

        try:
            fri_min = int(data.get('fridayReminderMinutes', DEFAULT_FRIDAY_REMINDER_MINUTES))
            if not (5 <= fri_min <= 240):
                fri_min = DEFAULT_FRIDAY_REMINDER_MINUTES
        except (TypeError, ValueError):
            fri_min = DEFAULT_FRIDAY_REMINDER_MINUTES

        wx = data.get('widgetX')
        wy = data.get('widgetY')
        tbx = data.get('topBarX')
        return cls(
            iqama_delays=delays,
            audio_enabled=bool(data.get('audioEnabled', True)),
            adhan_audio_path=str(data.get('adhanAudioPath', '') or ''),
            notifications_enabled=bool(data.get('notificationsEnabled', True)),
            friday_reminder_enabled=bool(data.get('fridayReminderEnabled', True)),
            friday_reminder_minutes=fri_min,
            lock_enabled=bool(data.get('lockEnabled', False)),
            custom_lock_command=str(data.get('customLockCommand', 'ft_lock') or 'ft_lock'),
            widget_x=wx if isinstance(wx, int) else None,
            widget_y=wy if isinstance(wy, int) else None,
            top_bar_mode=bool(data.get('topBarMode', True)),
            top_bar_x=tbx if isinstance(tbx, int) else None,
            position_locked=bool(data.get('positionLocked', False)),
            language=normalize_lang(data.get('language', 'en')),
        )


@dataclass
class PrayerEntry:
    key: str
    name: str
    time_str: str
    delay_minutes: int
    adhan_dt: datetime.datetime
    iqama_dt: datetime.datetime


@dataclass
class ActivePrayer:
    phase: str  # 'NEXT_ADHAN' or 'IQAMA'
    prayer: PrayerEntry
