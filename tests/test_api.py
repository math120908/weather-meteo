"""Tests for weather_meteo.api — factory + OpenMeteoBackend with mocked HTTP."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import MagicMock, patch

import pytest

from weather_meteo.api import get_backend
from weather_meteo.api.base import WeatherBackend
from weather_meteo.api.open_meteo import OpenMeteoBackend
from weather_meteo.config import LocationEntry


class TestGetBackend:
    """get_backend() factory returns the correct backend."""

    def test_open_meteo(self) -> None:
        backend = get_backend("open-meteo")
        assert isinstance(backend, OpenMeteoBackend)

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown backend"):
            get_backend("unknown")

    def test_passes_unit_and_model(self) -> None:
        backend = get_backend("open-meteo", unit="imperial", model="gfs_seamless")
        assert isinstance(backend, OpenMeteoBackend)
        assert backend._unit == "imperial"
        assert backend._model == "gfs_seamless"


class TestOpenMeteoBackendInit:
    """OpenMeteoBackend sets params based on unit/model."""

    def test_metric_defaults(self) -> None:
        b = OpenMeteoBackend()
        assert b._extra_params == {}

    def test_imperial_sets_units(self) -> None:
        b = OpenMeteoBackend(unit="imperial")
        assert b._extra_params["wind_speed_unit"] == "mph"
        assert b._extra_params["temperature_unit"] == "fahrenheit"

    def test_non_default_model(self) -> None:
        b = OpenMeteoBackend(model="gfs_seamless")
        assert b._extra_params["models"] == "gfs_seamless"

    def test_best_match_no_model_param(self) -> None:
        b = OpenMeteoBackend(model="best_match")
        assert "models" not in b._extra_params


class TestOpenMeteoBackendMocked:
    """OpenMeteoBackend methods with mocked httpx responses."""

    @pytest.fixture()
    def loc(self) -> LocationEntry:
        return LocationEntry(lat=53.35, lon=-6.26, label="Dublin")

    @pytest.fixture()
    def backend(self) -> OpenMeteoBackend:
        return OpenMeteoBackend(unit="metric", model="best_match")

    def _mock_response(self, json_data: dict) -> MagicMock:
        mock_resp = MagicMock()
        mock_resp.json.return_value = json_data
        mock_resp.raise_for_status.return_value = None
        return mock_resp

    @patch("weather_meteo.api.open_meteo.httpx.get")
    def test_get_current(
        self,
        mock_get: MagicMock,
        backend: OpenMeteoBackend,
        loc: LocationEntry,
    ) -> None:
        mock_get.return_value = self._mock_response({
            "current": {
                "temperature_2m": 18.5,
                "apparent_temperature": 17.0,
                "wind_speed_10m": 12.0,
                "wind_direction_10m": 225,
                "wind_gusts_10m": 20.0,
                "precipitation": 0.5,
                "relative_humidity_2m": 72,
                "weather_code": 3,
                "time": "2026-05-31T14:00",
            },
        })
        result = backend.get_current(loc)
        assert result.temperature == 18.5
        assert result.humidity == 72
        assert result.location_label == "Dublin"
        mock_get.assert_called_once()

    @patch("weather_meteo.api.open_meteo.httpx.get")
    def test_get_history(
        self,
        mock_get: MagicMock,
        backend: OpenMeteoBackend,
        loc: LocationEntry,
    ) -> None:
        mock_get.return_value = self._mock_response({
            "hourly": {
                "time": ["2026-01-01T00:00", "2026-01-01T01:00"],
                "temperature_2m": [5.0, 4.5],
                "wind_speed_10m": [10.0, 12.0],
                "wind_direction_10m": [180, 200],
                "precipitation": [0.0, 0.1],
            },
        })
        result = backend.get_history(loc, date(2026, 1, 1))
        assert len(result) == 2
        assert result[0].temperature == 5.0
        assert result[1].precipitation_probability == -1

    @patch("weather_meteo.api.open_meteo.httpx.get")
    def test_get_daily(
        self,
        mock_get: MagicMock,
        backend: OpenMeteoBackend,
        loc: LocationEntry,
    ) -> None:
        mock_get.return_value = self._mock_response({
            "daily": {
                "time": ["2026-06-01"],
                "temperature_2m_max": [22.0],
                "temperature_2m_min": [14.0],
                "precipitation_sum": [2.5],
                "precipitation_probability_max": [60],
                "wind_speed_10m_max": [25.0],
                "wind_gusts_10m_max": [40.0],
            },
            "hourly": {
                "time": ["2026-06-01T00:00", "2026-06-01T06:00"],
                "precipitation_probability": [20, 40],
            },
        })
        result = backend.get_daily(loc, days=1)
        assert len(result) == 1
        assert result[0].temp_max == 22.0
        assert len(result[0].hourly) == 2
