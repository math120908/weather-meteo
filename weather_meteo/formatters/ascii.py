from __future__ import annotations

from weather_meteo.models import (
    CurrentWeather,
    DailyEntry,
    HourlyEntry,
    rain_spark_char,
    weather_description,
    wind_arrow,
)


def _prob_bar(prob: int) -> str:
    n = max(0, (prob + 5) // 10)
    return "\u2591" * n


def _unit_suffix(unit: str) -> tuple[str, str]:
    if unit == "imperial":
        return "\u00b0F", "mph"
    return "\u00b0C", "km/h"


def format_now(current: CurrentWeather, unit: str = "metric") -> str:
    t_suf, w_suf = _unit_suffix(unit)
    arrow = wind_arrow(current.wind_direction)
    desc = weather_description(current.weather_code)
    feels = f" (\u2248 {current.feels_like:.0f}{t_suf})" if current.feels_like != current.temperature else ""
    return (
        f"{current.location_label} | "
        f"{current.temperature:.0f}{t_suf}{feels} | "
        f"{arrow} {current.wind_speed:.0f} {w_suf} | "
        f"{current.precipitation:.1f}mm | "
        f"{current.humidity}% | "
        f"{desc}"
    )


def format_hourly(
    entries: list[HourlyEntry],
    location_label: str,
    title: str = "Next 24h",
    unit: str = "metric",
    show_rain_col: bool = True,
    show_prob: bool = True,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    lines = [
        f"  {location_label} \u2014 {title}",
        "",
    ]
    if show_rain_col and show_prob:
        lines.append("  Time   Temp  Wind       Rain   Prob")
    elif show_prob:
        lines.append("  Time   Temp  Wind       Prob")
    else:
        lines.append("  Time   Temp  Wind       Rain")
    lines.append("  " + "\u2500" * 44)

    for e in entries:
        arrow = wind_arrow(e.wind_direction)
        time_str = e.time.strftime("%H:%M")
        temp_str = f"{e.temperature:.0f}{t_suf}"
        wind_str = f"{arrow} {e.wind_speed:>2.0f}{w_suf}"
        parts = [f"  {time_str}  {temp_str:>5}  {wind_str:>9}"]
        if show_rain_col:
            parts.append(f"{e.precipitation:>5.1f}mm")
        if show_prob:
            if e.precipitation_probability < 0:
                parts.append("   -")
            else:
                bar = _prob_bar(e.precipitation_probability)
                parts.append(f"{e.precipitation_probability:>4}% {bar}")
        lines.append("  ".join(parts))

    return "\n".join(lines)


def format_week(
    daily: list[DailyEntry],
    location_label: str,
    unit: str = "metric",
    detail: bool = False,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    lines = [
        f"  {location_label} \u2014 7-Day Forecast",
        "",
        "  Date        Hi/Lo    Wind     Rain   Prob",
        "  " + "\u2500" * 50,
    ]

    for d in daily:
        date_str = d.date.strftime("%a %d %b")
        hi_lo = f"{d.temp_max:.0f}/{d.temp_min:.0f}{t_suf}"
        wind = f"{d.wind_speed_max:.0f}{w_suf}"
        rain = f"{d.precipitation_sum:.1f}mm"
        prob = f"{d.precipitation_probability_max}%"
        lines.append(f"  {date_str:>10}  {hi_lo:>8}  {wind:>6}  {rain:>5}  {prob:>4}")

        if detail and d.hourly:
            for h in d.hourly:
                time_str = h.time.strftime("%H:%M")
                harrow = wind_arrow(h.wind_direction)
                bar = _prob_bar(h.precipitation_probability)
                lines.append(
                    f"    {time_str}  {h.temperature:.0f}{t_suf}  "
                    f"{harrow} {h.wind_speed:.0f}{w_suf}  "
                    f"{h.precipitation:.1f}mm  {h.precipitation_probability}% {bar}"
                )
            lines.append("")
        elif d.hourly:
            sparkline = "".join(rain_spark_char(h.precipitation_probability) for h in d.hourly)
            lines.append(f"  rain: {sparkline}")
            lines.append("        0         6        12        18")
            lines.append("")

    return "\n".join(lines)


def format_compare(
    currents: list[CurrentWeather],
    unit: str = "metric",
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    col_width = max(len(c.location_label) for c in currents) + 4
    col_width = max(col_width, 18)

    header = " " * 14 + "".join(c.location_label.ljust(col_width) for c in currents)
    sep = "  " + "\u2500" * (14 + col_width * len(currents))
    rows = [
        ("Temp", [f"{c.temperature:.0f}{t_suf}" for c in currents]),
        ("Feels like", [f"{c.feels_like:.0f}{t_suf}" for c in currents]),
        ("Wind", [f"{wind_arrow(c.wind_direction)} {c.wind_speed:.0f}{w_suf}" for c in currents]),
        ("Gusts", [f"{c.wind_gusts:.0f}{w_suf}" for c in currents]),
        ("Rain", [f"{c.precipitation:.1f}mm" for c in currents]),
        ("Humidity", [f"{c.humidity}%" for c in currents]),
        ("Condition", [weather_description(c.weather_code) for c in currents]),
    ]
    lines = [header, sep]
    for label, values in rows:
        line = f"  {label:<12}" + "".join(v.ljust(col_width) for v in values)
        lines.append(line)
    return "\n".join(lines)
