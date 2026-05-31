from dataclasses import dataclass, field
from datetime import date, datetime


FORECAST_MODELS = [
    ("best_match", "Auto-select best model (default)"),
    ("ecmwf_ifs025", "ECMWF IFS 0.25 — global, high quality"),
    ("gfs_seamless", "GFS — US model, global coverage"),
    ("icon_seamless", "ICON (DWD) — good for Europe"),
    ("gem_seamless", "GEM — Canadian model, global"),
    ("jma_seamless", "JMA — Japanese model, good for Asia"),
    ("ukmo_seamless", "UK Met Office — good for UK/Ireland"),
    ("knmi_harmonie_arome_europe", "KNMI HARMONIE — high-res Europe"),
    ("metno_nordic", "MET Norway Nordic — Scandinavia only"),
    ("bom_access_global", "BOM ACCESS — Australia"),
]

WIND_ARROWS = ["↑", "↗", "→", "↘", "↓", "↙", "←", "↖"]

RAIN_SPARK = ["▁", "▂", "▃", "▅", "▇", "█"]

WMO_DESCRIPTIONS = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def wind_arrow(degrees: int) -> str:
    index = round(degrees / 45) % 8
    return WIND_ARROWS[index]


def rain_spark_char(probability: int) -> str:
    if probability <= 10:
        return RAIN_SPARK[0]
    if probability <= 25:
        return RAIN_SPARK[1]
    if probability <= 40:
        return RAIN_SPARK[2]
    if probability <= 55:
        return RAIN_SPARK[3]
    if probability <= 75:
        return RAIN_SPARK[4]
    return RAIN_SPARK[5]


def weather_description(code: int) -> str:
    return WMO_DESCRIPTIONS.get(code, f"Unknown ({code})")


@dataclass
class CurrentWeather:
    temperature: float
    feels_like: float
    wind_speed: float
    wind_direction: int
    wind_gusts: float
    precipitation: float
    humidity: int
    weather_code: int
    time: datetime
    location_label: str = ""


@dataclass
class HourlyEntry:
    time: datetime
    temperature: float
    wind_speed: float
    wind_direction: int
    precipitation: float
    precipitation_probability: int
    # --full fields (None when not requested)
    humidity: int | None = None
    uv_index: float | None = None
    visibility: float | None = None  # meters
    pressure: float | None = None  # hPa
    cloud_cover: int | None = None  # %
    dewpoint: float | None = None


@dataclass
class DailyEntry:
    date: date
    temp_max: float
    temp_min: float
    precipitation_sum: float
    precipitation_probability_max: int
    wind_speed_max: float
    wind_gusts_max: float
    hourly: list[HourlyEntry] = field(default_factory=list)
    # --full fields
    sunrise: datetime | None = None
    sunset: datetime | None = None
    uv_index_max: float | None = None
