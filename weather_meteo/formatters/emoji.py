from __future__ import annotations

from weather_meteo.models import (
    CurrentWeather,
    DailyEntry,
    HourlyEntry,
    rain_spark_char,
    weather_description,
    wind_arrow,
)

WMO_EMOJI = {
    0: "\u2600\ufe0f", 1: "\U0001f324\ufe0f", 2: "\u26c5", 3: "\u2601\ufe0f",
    45: "\U0001f32b\ufe0f", 48: "\U0001f32b\ufe0f",
    51: "\U0001f326\ufe0f", 53: "\U0001f326\ufe0f", 55: "\U0001f327\ufe0f",
    56: "\U0001f328\ufe0f", 57: "\U0001f328\ufe0f",
    61: "\U0001f327\ufe0f", 63: "\U0001f327\ufe0f", 65: "\U0001f327\ufe0f",
    66: "\U0001f328\ufe0f", 67: "\U0001f328\ufe0f",
    71: "\u2744\ufe0f", 73: "\u2744\ufe0f", 75: "\u2744\ufe0f", 77: "\u2744\ufe0f",
    80: "\U0001f326\ufe0f", 81: "\U0001f327\ufe0f", 82: "\U0001f327\ufe0f",
    85: "\U0001f328\ufe0f", 86: "\U0001f328\ufe0f",
    95: "\u26c8\ufe0f", 96: "\u26c8\ufe0f", 99: "\u26c8\ufe0f",
}


def _emoji(code: int) -> str:
    return WMO_EMOJI.get(code, "\u2753")


def _unit_suffix(unit: str) -> tuple[str, str]:
    if unit == "imperial":
        return "\u00b0F", "mph"
    return "\u00b0C", "km/h"


def format_now(
    current: CurrentWeather,
    unit: str = "metric",
    hourly: list[HourlyEntry] | None = None,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    e = _emoji(current.weather_code)
    arrow = wind_arrow(current.wind_direction)
    lines = [
        f"{e} {current.location_label}: "
        f"{current.temperature:.0f}{t_suf} "
        f"\U0001f4a8{arrow}{current.wind_speed:.0f}{w_suf} "
        f"\U0001f4a7{current.precipitation:.1f}mm "
        f"\U0001f4a6{current.humidity}%"
    ]
    if hourly:
        lines.append("")
        for h in hourly:
            harrow = wind_arrow(h.wind_direction)
            prob = f"\u2614{h.precipitation_probability}%" if h.precipitation_probability >= 0 else ""
            lines.append(
                f"  {h.time.strftime('%H:%M')} "
                f"\U0001f321\ufe0f{h.temperature:.0f}{t_suf} "
                f"\U0001f4a8{harrow}{h.wind_speed:.0f}{w_suf} "
                f"{prob}"
            )
    return "\n".join(lines)


def _vis_km(meters: float) -> str:
    km = meters / 1000
    return f"{km:.0f}km" if km >= 10 else f"{km:.1f}km"


def format_hourly(
    entries: list[HourlyEntry],
    location_label: str,
    title: str = "Next 24h",
    unit: str = "metric",
    show_rain_col: bool = True,
    show_prob: bool = True,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    full = entries and entries[0].humidity is not None
    has_prob = entries and entries[0].precipitation_probability >= 0
    has_uv = full and any(e.uv_index is not None for e in entries)
    has_vis = full and any(e.visibility is not None for e in entries)

    lines = [f"\U0001f4cd {location_label} \u2014 {title}", ""]
    for e in entries:
        arrow = wind_arrow(e.wind_direction)
        time_str = e.time.strftime("%H:%M")
        parts = [
            f"  {time_str}",
            f"\U0001f321\ufe0f{e.temperature:.0f}{t_suf}",
            f"\U0001f4a8{arrow}{e.wind_speed:.0f}{w_suf}",
        ]
        if has_prob:
            parts.append(f"\u2614{e.precipitation_probability}%")
        if full:
            parts.append(f"\U0001f4a6{e.humidity}%")
            if has_uv:
                uv = f"{e.uv_index:.0f}" if e.uv_index is not None else "-"
                parts.append(f"\u2600\ufe0f{uv}")
            parts.append(f"\u2601\ufe0f{e.cloud_cover}%" if e.cloud_cover is not None else "")
            parts.append(f"\U0001f9ed{e.pressure:.0f}hPa" if e.pressure is not None else "")
            parts.append(f"\U0001f4a7{e.dewpoint:.0f}{t_suf}" if e.dewpoint is not None else "")
            if has_vis:
                parts.append(f"\U0001f441\ufe0f{_vis_km(e.visibility)}" if e.visibility is not None else "")
        lines.append(" ".join(p for p in parts if p))
    return "\n".join(lines)


def format_week(
    daily: list[DailyEntry],
    location_label: str,
    unit: str = "metric",
    detail: bool = False,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    full = daily and daily[0].sunrise is not None
    lines = [f"\U0001f4cd {location_label} \u2014 7-Day", ""]
    for d in daily:
        date_str = d.date.strftime("%a %d")
        spark = "".join(rain_spark_char(h.precipitation_probability) for h in d.hourly) if d.hourly else ""
        parts = [
            f"  {date_str}",
            f"\U0001f321\ufe0f{d.temp_max:.0f}/{d.temp_min:.0f}{t_suf}",
            f"\U0001f4a8{d.wind_speed_max:.0f}{w_suf}",
            f"\u2614{d.precipitation_probability_max}%",
        ]
        if full:
            if d.uv_index_max is not None:
                parts.append(f"\u2600\ufe0f{d.uv_index_max:.0f}")
            if d.sunrise and d.sunset:
                parts.append(f"\U0001f305{d.sunrise.strftime('%H:%M')}-{d.sunset.strftime('%H:%M')}")
        parts.append(spark)
        lines.append(" ".join(p for p in parts if p))
    return "\n".join(lines)


def format_model_compare(
    model_data: dict[str, list[HourlyEntry]],
    location_label: str,
    unit: str = "metric",
    hours: int = 24,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    model_names = list(model_data.keys())
    header = f"\U0001f4cd {location_label} — Model Comparison (next {hours}h)"
    col_header = "  Time  " + "".join(f"{m:>14}" for m in model_names)
    lines = [header, "", col_header]
    first_entries = model_data[model_names[0]]
    for i, e in enumerate(first_entries):
        parts = [f"  {e.time.strftime('%H:%M')}"]
        for m in model_names:
            entries_m = model_data[m]
            if i < len(entries_m):
                prob = entries_m[i].precipitation_probability
                parts.append(f"\u2614{prob:>3}%")
            else:
                parts.append("     -")
        lines.append("  ".join(parts))
    return "\n".join(lines)


def format_compare(
    currents: list[CurrentWeather],
    unit: str = "metric",
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    lines = []
    for c in currents:
        e = _emoji(c.weather_code)
        arrow = wind_arrow(c.wind_direction)
        lines.append(
            f"{e} {c.location_label}: "
            f"{c.temperature:.0f}{t_suf} "
            f"\U0001f4a8{arrow}{c.wind_speed:.0f}{w_suf} "
            f"\U0001f4a7{c.precipitation:.1f}mm "
            f"\U0001f4a6{c.humidity}%"
        )
    return "\n".join(lines)
