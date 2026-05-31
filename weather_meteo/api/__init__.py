from weather_meteo.api.base import WeatherBackend
from weather_meteo.api.open_meteo import OpenMeteoBackend


def get_backend(
    name: str = "open-meteo",
    unit: str = "metric",
    model: str = "best_match",
) -> WeatherBackend:
    if name == "open-meteo":
        return OpenMeteoBackend(unit=unit, model=model)
    raise ValueError(f"Unknown backend: {name!r}")
