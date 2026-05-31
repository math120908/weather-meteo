from __future__ import annotations

from io import StringIO

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

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


def _temp_color(temp: float) -> str:
    if temp <= 0:
        return "bright_cyan"
    if temp <= 10:
        return "cyan"
    if temp <= 18:
        return "green"
    if temp <= 25:
        return "yellow"
    if temp <= 32:
        return "bright_red"
    return "red"


def _prob_color(prob: int) -> str:
    if prob <= 20:
        return "green"
    if prob <= 50:
        return "yellow"
    if prob <= 75:
        return "bright_red"
    return "red"


def _wind_color(speed: float) -> str:
    if speed <= 15:
        return "green"
    if speed <= 30:
        return "yellow"
    if speed <= 50:
        return "bright_red"
    return "red"


def _render_rich(renderable) -> str:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=100)
    console.print(renderable)
    return buf.getvalue().rstrip()


def format_now(
    current: CurrentWeather,
    unit: str = "metric",
    hourly: list[HourlyEntry] | None = None,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    desc = weather_description(current.weather_code)
    arrow = wind_arrow(current.wind_direction)
    time_str = current.time.strftime("%a %d %b %H:%M")

    # Current conditions panel
    temp_c = _temp_color(current.temperature)
    wind_c = _wind_color(current.wind_speed)

    current_text = Text()
    current_text.append(f"  {desc}\n\n", style="bold")
    current_text.append(f"  Temp     ", style="dim")
    current_text.append(f"{current.temperature:.0f}{t_suf}", style=f"bold {temp_c}")
    if current.feels_like != current.temperature:
        current_text.append(f"  (feels {current.feels_like:.0f}{t_suf})", style="dim")
    current_text.append(f"\n  Wind     ", style="dim")
    current_text.append(f"{arrow} {current.wind_speed:.0f} {w_suf}", style=wind_c)
    current_text.append(f"  (gust {current.wind_gusts:.0f})", style="dim")
    current_text.append(f"\n  Rain     ", style="dim")
    current_text.append(f"{current.precipitation:.1f} mm\n", style="blue")
    current_text.append(f"  Humidity ", style="dim")
    current_text.append(f"{current.humidity}%", style="cyan")

    panel = Panel(
        current_text,
        title=f"[bold]{current.location_label}[/bold]  {time_str}",
        border_style="blue",
        width=50,
    )

    parts = [_render_rich(panel)]

    # 24h forecast table
    if hourly:
        table = Table(
            title="Next 24h",
            title_style="bold",
            border_style="dim",
            show_header=True,
            header_style="bold dim",
            pad_edge=False,
            width=60,
        )
        table.add_column("Time", style="dim", width=5)
        table.add_column("Temp", justify="right", width=5)
        table.add_column("Wind", width=10)
        table.add_column("Rain", justify="right", width=6)
        table.add_column("Prob", justify="right", width=4)
        table.add_column("", width=10)

        for e in hourly:
            earrow = wind_arrow(e.wind_direction)
            tc = _temp_color(e.temperature)
            pc = _prob_color(e.precipitation_probability)
            wc = _wind_color(e.wind_speed)
            bar = _prob_bar(e.precipitation_probability)

            table.add_row(
                e.time.strftime("%H:%M"),
                Text(f"{e.temperature:.0f}{t_suf}", style=tc),
                Text(f"{earrow} {e.wind_speed:.0f}{w_suf}", style=wc),
                Text(f"{e.precipitation:.1f}mm", style="blue" if e.precipitation > 0 else "dim"),
                Text(f"{e.precipitation_probability}%", style=pc),
                Text(bar, style=pc),
            )

        parts.append(_render_rich(table))

    return "\n".join(parts)


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
