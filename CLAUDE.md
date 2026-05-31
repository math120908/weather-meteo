# weather-meteo

CLI weather tool. Backend: Open-Meteo (free, no API key).

## Project Structure

```
weather_meteo/
├── cli.py              # click command group (entry point: main)
├── config.py           # YAML config at ~/.config/weather-meteo/config.yaml
├── location.py         # alias resolution + Open-Meteo geocoding fallback
├── models.py           # dataclasses (CurrentWeather, HourlyEntry, DailyEntry) + helpers
├── api/
│   ├── base.py         # WeatherBackend ABC
│   └── open_meteo.py   # Open-Meteo implementation
└── formatters/
    ├── ascii.py        # colored terminal tables with rain bars
    ├── emoji.py        # compact emoji display
    └── json_fmt.py     # raw JSON output
```

## Key Patterns

- **Backend abstraction**: All backends implement `WeatherBackend` ABC and return unified dataclasses from `models.py`. To add a new backend, implement the ABC and register in `api/__init__.py`.
- **Formatter interface**: Each formatter module exposes `format_now()`, `format_hourly()`, `format_week()`, `format_compare()` with the same signatures.
- **Location resolution**: alias lookup in config → Open-Meteo geocoding API → error.
- **Global options** (`--location`, `--format`) are on the click group, passed via `ctx.obj`.

## Commands

`weather-meteo` (default=now) | `hourly` | `week [--detail]` | `run [--hours N]` | `compare LOC1 LOC2` | `history --date YYYY-MM-DD` | `config setup|edit|show`

## Development

```bash
pip install -e ~/project/weather-meteo
weather-meteo --help
```
