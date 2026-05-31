# weather-meteo

CLI weather tool powered by [Open-Meteo](https://open-meteo.com/). Free, no API key required.

## Demo

![weather-meteo demo](docs/demo/demo.gif)

## Install

```bash
git clone https://github.com/math120908/weather-meteo.git
pip install -e .
```

## Quick Start

```bash
weather-meteo config setup                   # interactive first-time setup
weather-meteo                                # next 24h hourly forecast (default)
weather-meteo hourly -H 6                    # next 6h only
weather-meteo week                           # 7-day forecast with rain heatmap
weather-meteo week --detail                  # 7-day with full hourly breakdown
weather-meteo compare sandymount taipei      # multi-location comparison
weather-meteo history --date 2026-05-01      # historical weather
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--location LOC` | `-l` | Location alias or city name |
| `--format FMT` | `-f` | `ascii` (default), `emoji`, `json` |
| `--hours N` | `-H` | Hour range for `hourly` (default 24) |

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

Manage with `weather-meteo config setup|add|edit|show`.

```bash
# Add a location by searching
weather-meteo config add --name home "dublin 2"
#   [1] Dublin 2, Leinster, Ireland (53.33941, -6.25116)
#   [2] Dublin, Leinster, Ireland (53.33306, -6.24889)
#   ...
#   Select [1]:
# Added 'home' -> Dublin 2, Leinster, Ireland
```

## Architecture

Modular backend design — swap or add weather APIs without touching CLI or formatters.

```
cli.py → api/base.py (ABC) → models.py → formatters/
              ↑
         open_meteo.py
         (future: met_norway.py, owm.py, ...)
```
