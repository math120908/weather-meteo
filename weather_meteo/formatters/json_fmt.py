from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime

from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry, weather_description


class _Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, date):
            return o.isoformat()
        return super().default(o)


def _dump(obj) -> str:
    return json.dumps(obj, cls=_Encoder, indent=2, ensure_ascii=False)


def format_now(current: CurrentWeather, unit: str = "metric") -> str:
    d = asdict(current)
    d["weather_description"] = weather_description(current.weather_code)
    return _dump(d)


def format_hourly(
    entries: list[HourlyEntry],
    location_label: str,
    title: str = "Next 24h",
    unit: str = "metric",
    show_rain_col: bool = True,
    show_prob: bool = True,
) -> str:
    return _dump({
        "location": location_label,
        "title": title,
        "entries": [asdict(e) for e in entries],
    })


def format_week(
    daily: list[DailyEntry],
    location_label: str,
    unit: str = "metric",
    detail: bool = False,
) -> str:
    return _dump({
        "location": location_label,
        "daily": [asdict(d) for d in daily],
    })


def format_compare(
    currents: list[CurrentWeather],
    unit: str = "metric",
) -> str:
    return _dump({
        "locations": [
            {**asdict(c), "weather_description": weather_description(c.weather_code)}
            for c in currents
        ],
    })
