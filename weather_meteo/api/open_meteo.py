from __future__ import annotations

from datetime import date, datetime

import httpx

from weather_meteo.api.base import WeatherBackend
from weather_meteo.config import LocationEntry
from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"


class OpenMeteoBackend(WeatherBackend):
    def __init__(self, unit: str = "metric", model: str = "best_match") -> None:
        self._unit = unit
        self._model = model
        self._extra_params: dict[str, str] = {}
        if unit == "imperial":
            self._extra_params["wind_speed_unit"] = "mph"
            self._extra_params["temperature_unit"] = "fahrenheit"
        if model and model != "best_match":
            self._extra_params["models"] = model

    def _get(self, url: str, params: dict) -> dict:
        params = {**params, **self._extra_params, "timezone": "auto"}
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_current(self, location: LocationEntry) -> CurrentWeather:
        data = self._get(FORECAST_URL, {
            "latitude": location.lat,
            "longitude": location.lon,
            "current": ",".join([
                "temperature_2m",
                "apparent_temperature",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m",
                "precipitation",
                "relative_humidity_2m",
                "weather_code",
            ]),
        })
        c = data["current"]
        return CurrentWeather(
            temperature=c["temperature_2m"],
            feels_like=c["apparent_temperature"],
            wind_speed=c["wind_speed_10m"],
            wind_direction=int(c["wind_direction_10m"]),
            wind_gusts=c["wind_gusts_10m"],
            precipitation=c["precipitation"],
            humidity=int(c["relative_humidity_2m"]),
            weather_code=int(c["weather_code"]),
            time=datetime.fromisoformat(c["time"]),
            location_label=location.label,
        )

    def get_hourly(self, location: LocationEntry, hours: int = 24) -> list[HourlyEntry]:
        data = self._get(FORECAST_URL, {
            "latitude": location.lat,
            "longitude": location.lon,
            "hourly": ",".join([
                "temperature_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation",
                "precipitation_probability",
            ]),
            "forecast_days": min((hours // 24) + 1, 16),
        })
        h = data["hourly"]
        now = datetime.now().astimezone()
        entries = []
        for i, time_str in enumerate(h["time"]):
            t = datetime.fromisoformat(time_str)
            if t.tzinfo is None:
                t = t.replace(tzinfo=now.tzinfo)
            if t < now:
                continue
            if len(entries) >= hours:
                break
            entries.append(HourlyEntry(
                time=t,
                temperature=h["temperature_2m"][i],
                wind_speed=h["wind_speed_10m"][i],
                wind_direction=int(h["wind_direction_10m"][i]),
                precipitation=h["precipitation"][i],
                precipitation_probability=int(h["precipitation_probability"][i]),
            ))
        return entries

    def get_daily(self, location: LocationEntry, days: int = 7, detail: bool = False) -> list[DailyEntry]:
        hourly_fields = ["precipitation_probability"]
        if detail:
            hourly_fields += [
                "temperature_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation",
            ]
        data = self._get(FORECAST_URL, {
            "latitude": location.lat,
            "longitude": location.lon,
            "daily": ",".join([
                "temperature_2m_max",
                "temperature_2m_min",
                "precipitation_sum",
                "precipitation_probability_max",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
            ]),
            "hourly": ",".join(hourly_fields),
            "forecast_days": days,
        })
        d = data["daily"]
        h = data.get("hourly", {})
        hourly_probs = h.get("precipitation_probability", [])
        hourly_times = h.get("time", [])
        hourly_temps = h.get("temperature_2m", [])
        hourly_winds = h.get("wind_speed_10m", [])
        hourly_dirs = h.get("wind_direction_10m", [])
        hourly_precip = h.get("precipitation", [])

        entries = []
        for i in range(len(d["time"])):
            day_date = date.fromisoformat(d["time"][i])
            day_hourly: list[HourlyEntry] = []
            for j, t_str in enumerate(hourly_times):
                t = datetime.fromisoformat(t_str)
                if t.date() == day_date and j < len(hourly_probs):
                    day_hourly.append(HourlyEntry(
                        time=t,
                        temperature=hourly_temps[j] if hourly_temps else 0,
                        wind_speed=hourly_winds[j] if hourly_winds else 0,
                        wind_direction=int(hourly_dirs[j]) if hourly_dirs else 0,
                        precipitation=hourly_precip[j] if hourly_precip else 0,
                        precipitation_probability=int(hourly_probs[j]),
                    ))
            entries.append(DailyEntry(
                date=day_date,
                temp_max=d["temperature_2m_max"][i],
                temp_min=d["temperature_2m_min"][i],
                precipitation_sum=d["precipitation_sum"][i],
                precipitation_probability_max=int(d["precipitation_probability_max"][i]),
                wind_speed_max=d["wind_speed_10m_max"][i],
                wind_gusts_max=d["wind_gusts_10m_max"][i],
                hourly=day_hourly,
            ))
        return entries

    def get_history(self, location: LocationEntry, target_date: date) -> list[HourlyEntry]:
        data = self._get(ARCHIVE_URL, {
            "latitude": location.lat,
            "longitude": location.lon,
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
            "hourly": ",".join([
                "temperature_2m",
                "wind_speed_10m",
                "wind_direction_10m",
                "precipitation",
            ]),
        })
        h = data["hourly"]
        entries = []
        for i, time_str in enumerate(h["time"]):
            entries.append(HourlyEntry(
                time=datetime.fromisoformat(time_str),
                temperature=h["temperature_2m"][i],
                wind_speed=h["wind_speed_10m"][i],
                wind_direction=int(h["wind_direction_10m"][i]),
                precipitation=h["precipitation"][i],
                precipitation_probability=-1,
            ))
        return entries
