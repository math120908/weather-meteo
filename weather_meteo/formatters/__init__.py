from __future__ import annotations


def get_formatter(name: str):
    if name == "ascii":
        from weather_meteo.formatters import ascii as fmt
        return fmt
    if name == "emoji":
        from weather_meteo.formatters import emoji as fmt
        return fmt
    if name == "json":
        from weather_meteo.formatters import json_fmt as fmt
        return fmt
    raise ValueError(f"Unknown format: {name!r}")
