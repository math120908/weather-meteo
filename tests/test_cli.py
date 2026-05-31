"""Tests for weather_meteo.cli — click CliRunner smoke tests."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from weather_meteo.cli import main
from weather_meteo.config import Config, LocationEntry
from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture()
def mock_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Config:
    """Provide a config that doesn't touch real filesystem."""
    config_dir = tmp_path / "weather-meteo"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr("weather_meteo.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)
    monkeypatch.setattr("weather_meteo.cli.CONFIG_FILE", config_file)
    cfg = Config(
        default_location="dublin",
        unit="metric",
        format="json",
        locations={
            "dublin": LocationEntry(lat=53.35, lon=-6.26, label="Dublin"),
        },
    )
    return cfg


def _fake_current() -> CurrentWeather:
    return CurrentWeather(
        temperature=18.0,
        feels_like=17.0,
        wind_speed=12.0,
        wind_direction=225,
        wind_gusts=20.0,
        precipitation=0.5,
        humidity=72,
        weather_code=3,
        time=datetime(2026, 5, 31, 14, 0),
        location_label="Dublin",
    )


def _fake_hourly() -> list[HourlyEntry]:
    return [HourlyEntry(
        time=datetime(2026, 5, 31, 15, 0),
        temperature=19.0,
        wind_speed=10.0,
        wind_direction=180,
        precipitation=0.0,
        precipitation_probability=20,
    )]


class TestListModels:
    """--list-models flag."""

    def test_list_models(self, runner: CliRunner) -> None:
        result = runner.invoke(main, ["--list-models"])
        assert result.exit_code == 0
        assert "best_match" in result.output
        assert "ecmwf_ifs025" in result.output


class TestHourlyCommand:
    """'hourly' subcommand smoke test."""

    @patch("weather_meteo.cli.load_config")
    @patch("weather_meteo.cli.get_backend")
    def test_hourly_json(
        self,
        mock_get_backend: MagicMock,
        mock_load: MagicMock,
        runner: CliRunner,
        mock_config: Config,
    ) -> None:
        mock_load.return_value = mock_config
        mock_backend = MagicMock()
        mock_backend.get_hourly.return_value = _fake_hourly()
        mock_get_backend.return_value = mock_backend

        result = runner.invoke(main, ["-f", "json", "hourly"])
        assert result.exit_code == 0
        assert "18" in result.output


class TestConfigShow:
    """'config show' subcommand."""

    def test_config_show_no_file(
        self,
        runner: CliRunner,
        mock_config: Config,
    ) -> None:
        result = runner.invoke(main, ["config", "show"])
        assert result.exit_code == 0
        assert "No config file" in result.output
