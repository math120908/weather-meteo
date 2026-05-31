from weather_meteo.api.base import WeatherBackend
from weather_meteo.api.open_meteo import OpenMeteoBackend


def get_backend(name: str = "open-meteo", unit: str = "metric") -> WeatherBackend:
    if name == "open-meteo":
        return OpenMeteoBackend(unit=unit)
    raise ValueError(f"Unknown backend: {name!r}")
