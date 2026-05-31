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


def _render_rich(renderable, width: int = 100) -> str:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=width)
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

    if hourly:
        parts.append(_build_hourly_table(hourly, "Next 24h", t_suf, w_suf))

    return "\n".join(parts)


def _build_hourly_table(
    entries: list[HourlyEntry],
    title: str,
    t_suf: str,
    w_suf: str,
) -> str:
    table = Table(
        title=title,
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

    for e in entries:
        earrow = wind_arrow(e.wind_direction)
        tc = _temp_color(e.temperature)
        wc = _wind_color(e.wind_speed)

        if e.precipitation_probability < 0:
            prob_text = Text("-", style="dim")
            bar_text = Text("")
        else:
            pc = _prob_color(e.precipitation_probability)
            prob_text = Text(f"{e.precipitation_probability}%", style=pc)
            bar_text = Text(_prob_bar(e.precipitation_probability), style=pc)

        table.add_row(
            e.time.strftime("%H:%M"),
            Text(f"{e.temperature:.0f}{t_suf}", style=tc),
            Text(f"{earrow} {e.wind_speed:.0f}{w_suf}", style=wc),
            Text(f"{e.precipitation:.1f}mm", style="blue" if e.precipitation > 0 else "dim"),
            prob_text,
            bar_text,
        )

    return _render_rich(table)


def format_model_compare(
    model_data: dict[str, list[HourlyEntry]],
    location_label: str,
    unit: str = "metric",
    hours: int = 24,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    model_names = list(model_data.keys())

    title = f"Model Comparison — {location_label} (next {hours}h)"

    table = Table(
        title=title,
        title_style="bold",
        border_style="dim",
        show_header=True,
        header_style="bold dim",
        pad_edge=False,
    )
    table.add_column("Time", style="dim", no_wrap=True)
    table.add_column("Temp", justify="right", no_wrap=True)
    table.add_column("Wind", no_wrap=True)
    for m in model_names:
        table.add_column(m, justify="right", min_width=14, no_wrap=True)

    # Use first model for temp/wind (they're similar across models)
    # Show rain probability from each model as columns
    first_entries = model_data[model_names[0]]
    for i, e in enumerate(first_entries):
        row: list[str | Text] = [
            e.time.strftime("%H:%M"),
            Text(f"{e.temperature:.0f}{t_suf}", style=_temp_color(e.temperature)),
            Text(f"{wind_arrow(e.wind_direction)} {e.wind_speed:.0f}{w_suf}", style=_wind_color(e.wind_speed)),
        ]
        for m in model_names:
            entries_m = model_data[m]
            if i < len(entries_m):
                prob = entries_m[i].precipitation_probability
                pc = _prob_color(prob)
                bar = _prob_bar(prob)
                row.append(Text(f"{prob}% {bar}", style=pc))
            else:
                row.append(Text("-", style="dim"))
        table.add_row(*row)

    render_width = 40 + 16 * len(model_names)
    return _render_rich(table, width=max(100, render_width))


def format_hourly(
    entries: list[HourlyEntry],
    location_label: str,
    title: str = "Next 24h",
    unit: str = "metric",
    show_rain_col: bool = True,
    show_prob: bool = True,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)
    full_title = f"{location_label} \u2014 {title}"
    return _build_hourly_table(entries, full_title, t_suf, w_suf)


def _colored_sparkline(hourly: list[HourlyEntry]) -> Text:
    spark = Text()
    for i, h in enumerate(hourly):
        if i > 0 and i % 6 == 0:
            spark.append(" ")
        char = rain_spark_char(h.precipitation_probability)
        color = _prob_color(h.precipitation_probability)
        spark.append(char, style=color)
    return spark


def _sparkline_scale() -> Text:
    # Aligned with sparkline: 6 chars + space pattern
    # "0     6     12    18    24"
    scale = Text()
    scale.append("0     ", style="dim")
    scale.append(" 6    ", style="dim")
    scale.append(" 12   ", style="dim")
    scale.append(" 18   ", style="dim")
    scale.append(" 24", style="dim")
    return scale


def format_week(
    daily: list[DailyEntry],
    location_label: str,
    unit: str = "metric",
    detail: bool = False,
) -> str:
    t_suf, w_suf = _unit_suffix(unit)

    if detail:
        # Detail mode: summary table then per-day hourly tables
        parts = []
        for d in daily:
            date_str = d.date.strftime("%a %d %b")
            title = f"{date_str}  {d.temp_max:.0f}/{d.temp_min:.0f}{t_suf}"
            if d.hourly:
                parts.append(_build_hourly_table(d.hourly, title, t_suf, w_suf))
            else:
                parts.append(title)
        return "\n\n".join(parts)

    table = Table(
        title=f"{location_label} \u2014 7-Day Forecast",
        title_style="bold",
        border_style="dim",
        show_header=True,
        header_style="bold dim",
        pad_edge=False,
        width=80,
    )
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Hi/Lo", justify="right", no_wrap=True)
    table.add_column("Wind", justify="right", no_wrap=True)
    table.add_column("Rain", justify="right", no_wrap=True)
    table.add_column("Prob", justify="right", no_wrap=True)
    table.add_column("Hourly Rain", no_wrap=True, min_width=24)

    for d in daily:
        date_str = d.date.strftime("%a %d %b")
        tc_hi = _temp_color(d.temp_max)
        tc_lo = _temp_color(d.temp_min)
        hi_lo = Text()
        hi_lo.append(f"{d.temp_max:.0f}", style=tc_hi)
        hi_lo.append("/")
        hi_lo.append(f"{d.temp_min:.0f}{t_suf}", style=tc_lo)

        wc = _wind_color(d.wind_speed_max)
        pc = _prob_color(d.precipitation_probability_max)

        spark = _colored_sparkline(d.hourly) if d.hourly else Text("")

        table.add_row(
            date_str,
            hi_lo,
            Text(f"{d.wind_speed_max:.0f}{w_suf}", style=wc),
            Text(f"{d.precipitation_sum:.1f}mm", style="blue" if d.precipitation_sum > 0 else "dim"),
            Text(f"{d.precipitation_probability_max}%", style=pc),
            spark,
        )

    # Add time scale footer row
    table.add_row("", "", "", "", "", _sparkline_scale(), end_section=True)

    return _render_rich(table)


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
