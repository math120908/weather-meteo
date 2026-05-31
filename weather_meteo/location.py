from __future__ import annotations

import click
import httpx

from weather_meteo.config import Config, LocationEntry


def resolve_location(name: str | None, config: Config) -> LocationEntry:
    if name is None:
        name = config.default_location
    if not name:
        raise click.ClickException(
            "No location specified. Use --location or run 'weather-meteo config setup'."
        )
    if name in config.locations:
        return config.locations[name]
    return _geocode(name)


def _geocode(name: str) -> LocationEntry:
    results = geocode_search(name, count=1)
    if not results:
        raise click.ClickException(f"Location not found: {name!r}")
    return results[0]


def geocode_search(name: str, count: int = 5) -> list[LocationEntry]:
    """Search for locations by name, returning up to *count* results."""
    url = "https://geocoding-api.open-meteo.com/v1/search"
    resp = httpx.get(url, params={"name": name, "count": count}, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    raw_results = data.get("results")
    if not raw_results:
        return []
    entries: list[LocationEntry] = []
    for r in raw_results:
        parts = [r.get("name", name)]
        if r.get("admin1"):
            parts.append(r["admin1"])
        if r.get("country"):
            parts.append(r["country"])
        label = ", ".join(parts)
        entries.append(LocationEntry(lat=r["latitude"], lon=r["longitude"], label=label))
    return entries


def detect_current_location() -> LocationEntry:
    resp = httpx.get("https://ipinfo.io/json", timeout=10)
    resp.raise_for_status()
    data = resp.json()
    loc_str = data.get("loc", "0,0")
    lat_str, lon_str = loc_str.split(",")
    city = data.get("city", "Unknown")
    region = data.get("region", "")
    country = data.get("country", "")
    parts = [p for p in [city, region, country] if p]
    return LocationEntry(
        lat=float(lat_str),
        lon=float(lon_str),
        label=", ".join(parts),
    )
