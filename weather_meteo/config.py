from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

import yaml


CONFIG_DIR = Path(os.environ.get("WEATHER_METEO_CONFIG_DIR", Path.home() / ".config" / "weather-meteo"))
CONFIG_FILE = CONFIG_DIR / "config.yaml"

def _build_config_header() -> str:
    from weather_meteo.models import FORECAST_MODELS
    lines = [
        "# weather-meteo configuration",
        "#",
        "# ── defaults ──────────────────────────────────────────────",
        "#   location: <alias>         default location alias",
        "#   unit: metric | imperial   temperature & wind units",
        "#   format: ascii | emoji | json",
        "#   backend: open-meteo       (only option for now)",
        "#   model: <model_id>         global default forecast model",
        "#",
        "# ── Available models (Open-Meteo) ─────────────────────────",
    ]
    for model_id, desc in FORECAST_MODELS:
        lines.append(f"#   {model_id:<35} {desc}")
    lines += [
        "#",
        "#   Tip: icon_seamless works well for Ireland/Europe.",
        "#        For Asia, try jma_seamless or best_match.",
        "#",
        "# ── locations ─────────────────────────────────────────────",
        "#   <alias>:",
        "#     lat: <latitude>",
        "#     lon: <longitude>",
        '#     label: "<display name>"',
        "#     model: <model_id>       (optional, overrides default)",
        "#",
    ]
    return "\n".join(lines) + "\n"


@dataclass
class LocationEntry:
    lat: float
    lon: float
    label: str
    model: str = ""


@dataclass
class Config:
    default_location: str = ""
    unit: str = "metric"
    format: str = "ascii"
    backend: str = "open-meteo"
    model: str = "best_match"
    locations: dict[str, LocationEntry] = field(default_factory=dict)


def load_config() -> Config:
    if not CONFIG_FILE.exists():
        return Config()
    with open(CONFIG_FILE) as f:
        raw = yaml.safe_load(f) or {}
    defaults = raw.get("defaults", {})
    locations_raw = raw.get("locations", {})
    locations = {}
    for alias, loc in locations_raw.items():
        locations[alias] = LocationEntry(
            lat=loc["lat"],
            lon=loc["lon"],
            label=loc.get("label", alias),
            model=loc.get("model", ""),
        )
    return Config(
        default_location=defaults.get("location", ""),
        unit=defaults.get("unit", "metric"),
        format=defaults.get("format", "ascii"),
        backend=defaults.get("backend", "open-meteo"),
        model=defaults.get("model", "best_match"),
        locations=locations,
    )


def save_config(config: Config) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    locations_raw = {}
    for alias, loc in config.locations.items():
        entry: dict = {
            "lat": loc.lat,
            "lon": loc.lon,
            "label": loc.label,
        }
        if loc.model:
            entry["model"] = loc.model
        locations_raw[alias] = entry
    data = {
        "defaults": {
            "location": config.default_location,
            "unit": config.unit,
            "format": config.format,
            "backend": config.backend,
            "model": config.model,
        },
        "locations": locations_raw,
    }
    with open(CONFIG_FILE, "w") as f:
        f.write(_build_config_header())
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)


def edit_config() -> None:
    if not CONFIG_FILE.exists():
        save_config(Config())
    editor = os.environ.get("EDITOR", "vim")
    subprocess.run([editor, str(CONFIG_FILE)], check=True)
