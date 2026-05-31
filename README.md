# weather-meteo

CLI weather tool powered by [Open-Meteo](https://open-meteo.com/). Free, no API key required.

## Install

```bash
git clone https://github.com/math120908/weather-meteo.git
pip install -e .
```

## Quick Start

```bash
weather-meteo config setup                   # interactive first-time setup
weather-meteo                                # current weather (default location)
weather-meteo hourly                         # next 24h hourly forecast
weather-meteo week                           # 7-day forecast with rain heatmap
weather-meteo week --detail                  # 7-day with full hourly breakdown
weather-meteo run                            # run check (next 6h)
weather-meteo run --hours 3                  # run check (next 3h)
weather-meteo compare sandymount taipei      # multi-location comparison
weather-meteo history --date 2026-05-01      # historical weather
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--location LOC` | `-l` | Location alias or city name |
| `--format FMT` | `-f` | `ascii` (default), `emoji`, `json` |
| `--hours N` | `-H` | Override hour range (for `run`) |

## Config

Stored at `~/.config/weather-meteo/config.yaml`.

```yaml
defaults:
  location: sandymount
  unit: metric        # metric | imperial
  format: ascii       # ascii | emoji | json
  backend: open-meteo

locations:
  sandymount:
    lat: 53.328
    lon: -6.222
    label: "Sandymount, Dublin"
  taipei:
    lat: 25.033
    lon: 121.565
    label: "Taipei"
```

Manage with `weather-meteo config setup|edit|show`.

## Architecture

Modular backend design — swap or add weather APIs without touching CLI or formatters.

```
cli.py → api/base.py (ABC) → models.py → formatters/
              ↑
         open_meteo.py
         (future: met_norway.py, owm.py, ...)
```
