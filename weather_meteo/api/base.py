from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date

from weather_meteo.config import LocationEntry
from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry


class WeatherBackend(ABC):
    @abstractmethod
    def get_current(self, location: LocationEntry) -> CurrentWeather: ...

    @abstractmethod
    def get_hourly(self, location: LocationEntry, hours: int) -> list[HourlyEntry]: ...

    @abstractmethod
    def get_daily(self, location: LocationEntry, days: int, detail: bool = False) -> list[DailyEntry]: ...

    @abstractmethod
    def get_history(self, location: LocationEntry, target_date: date) -> list[HourlyEntry]: ...
