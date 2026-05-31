"""Shared fixtures for weather-meteo tests."""

from __future__ import annotations

from datetime import date, datetime

import pytest

from weather_meteo.config import Config, LocationEntry
from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry


@pytest.fixture()
def sample_location() -> LocationEntry:
    return LocationEntry(lat=53.35, lon=-6.26, label="Dublin, Leinster, Ireland")


@pytest.fixture()
def sample_config(sample_location: LocationEntry) -> Config:
    return Config(
        default_location="dublin",
        unit="metric",
        format="ascii",
        backend="open-meteo",
        model="best_match",
        locations={"dublin": sample_location},
    )


@pytest.fixture()
def sample_current() -> CurrentWeather:
    return CurrentWeather(
        temperature=18.5,
        feels_like=17.0,
        wind_speed=12.3,
        wind_direction=225,
        wind_gusts=20.1,
        precipitation=0.5,
        humidity=72,
        weather_code=3,
        time=datetime(2026, 5, 31, 14, 0),
        location_label="Dublin, Leinster, Ireland",
    )


@pytest.fixture()
def sample_hourly_entries() -> list[HourlyEntry]:
    base = datetime(2026, 5, 31, 14, 0)
    entries = []
    for i in range(6):
        entries.append(HourlyEntry(
            time=datetime(
                base.year, base.month, base.day,
                base.hour + i, 0,
            ),
            temperature=18.0 + i * 0.5,
            wind_speed=10.0 + i,
            wind_direction=180 + i * 30,
            precipitation=0.1 * i,
            precipitation_probability=10 * i,
        ))
    return entries


@pytest.fixture()
def sample_daily_entries(sample_hourly_entries: list[HourlyEntry]) -> list[DailyEntry]:
    return [
        DailyEntry(
            date=date(2026, 5, 31),
            temp_max=22.0,
            temp_min=14.0,
            precipitation_sum=2.5,
            precipitation_probability_max=60,
            wind_speed_max=25.0,
            wind_gusts_max=40.0,
            hourly=sample_hourly_entries,
        ),
        DailyEntry(
            date=date(2026, 6, 1),
            temp_max=20.0,
            temp_min=12.0,
            precipitation_sum=0.0,
            precipitation_probability_max=10,
            wind_speed_max=15.0,
            wind_gusts_max=22.0,
            hourly=[],
        ),
    ]
