"""Tests for all three formatters (json, emoji, ascii)."""

from __future__ import annotations

import json

import pytest

from weather_meteo.formatters import get_formatter
from weather_meteo.models import CurrentWeather, DailyEntry, HourlyEntry


# ── Factory tests ──────────────────────────────────────────────────────


class TestGetFormatter:
    """get_formatter() returns the correct module."""

    def test_ascii(self) -> None:
        fmt = get_formatter("ascii")
        assert hasattr(fmt, "format_now")

    def test_emoji(self) -> None:
        fmt = get_formatter("emoji")
        assert hasattr(fmt, "format_now")

    def test_json(self) -> None:
        fmt = get_formatter("json")
        assert hasattr(fmt, "format_now")

    def test_unknown_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown format"):
            get_formatter("xml")


# ── JSON formatter ─────────────────────────────────────────────────────


class TestJsonFormatter:
    """JSON formatter produces valid JSON with expected keys."""

    @pytest.fixture()
    def fmt(self):
        return get_formatter("json")

    def test_format_now(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_now(sample_current, unit="metric")
        data = json.loads(result)
        assert data["temperature"] == 18.5
        assert data["weather_description"] == "Overcast"
        assert "hourly" not in data

    def test_format_now_with_hourly(
        self,
        fmt,
        sample_current: CurrentWeather,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_now(sample_current, unit="metric", hourly=sample_hourly_entries)
        data = json.loads(result)
        assert "hourly" in data
        assert len(data["hourly"]) == 6

    def test_format_hourly(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_hourly(sample_hourly_entries, "Dublin", title="Test")
        data = json.loads(result)
        assert data["location"] == "Dublin"
        assert data["title"] == "Test"
        assert len(data["entries"]) == 6

    def test_format_week(
        self,
        fmt,
        sample_daily_entries: list[DailyEntry],
    ) -> None:
        result = fmt.format_week(sample_daily_entries, "Dublin")
        data = json.loads(result)
        assert data["location"] == "Dublin"
        assert len(data["daily"]) == 2

    def test_format_compare(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_compare([sample_current, sample_current])
        data = json.loads(result)
        assert len(data["locations"]) == 2
        assert data["locations"][0]["weather_description"] == "Overcast"

    def test_format_model_compare(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        model_data = {
            "model_a": sample_hourly_entries,
            "model_b": sample_hourly_entries[:3],
        }
        result = fmt.format_model_compare(model_data, "Dublin")
        data = json.loads(result)
        assert "model_a" in data["models"]
        assert len(data["models"]["model_b"]) == 3


# ── Emoji formatter ────────────────────────────────────────────────────


class TestEmojiFormatter:
    """Emoji formatter produces text with expected content."""

    @pytest.fixture()
    def fmt(self):
        return get_formatter("emoji")

    def test_format_now(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_now(sample_current, unit="metric")
        assert "Dublin" in result
        assert "18" in result  # temperature ~18.5 rounds to 18

    def test_format_now_imperial(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_now(sample_current, unit="imperial")
        assert "mph" in result

    def test_format_now_with_hourly(
        self,
        fmt,
        sample_current: CurrentWeather,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_now(sample_current, hourly=sample_hourly_entries)
        # Should have multiple lines for hourly entries
        lines = result.strip().split("\n")
        assert len(lines) > 2

    def test_format_hourly(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_hourly(sample_hourly_entries, "Dublin")
        assert "Dublin" in result
        assert "Next 24h" in result

    def test_format_week(
        self,
        fmt,
        sample_daily_entries: list[DailyEntry],
    ) -> None:
        result = fmt.format_week(sample_daily_entries, "Dublin")
        assert "Dublin" in result
        assert "7-Day" in result

    def test_format_compare(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_compare([sample_current])
        assert "Dublin" in result

    def test_format_model_compare(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        model_data = {"gfs": sample_hourly_entries, "icon": sample_hourly_entries}
        result = fmt.format_model_compare(model_data, "Dublin", hours=6)
        assert "Dublin" in result
        assert "gfs" in result


# ── ASCII (rich) formatter ─────────────────────────────────────────────


class TestAsciiFormatter:
    """ASCII formatter (rich tables/panels) produces text output."""

    @pytest.fixture()
    def fmt(self):
        return get_formatter("ascii")

    def test_format_now(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_now(sample_current, unit="metric")
        assert "Dublin" in result
        assert "Overcast" in result

    def test_format_now_with_hourly(
        self,
        fmt,
        sample_current: CurrentWeather,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_now(sample_current, hourly=sample_hourly_entries)
        assert "Next 24h" in result

    def test_format_hourly(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        result = fmt.format_hourly(sample_hourly_entries, "Dublin")
        assert "Dublin" in result

    def test_format_week(
        self,
        fmt,
        sample_daily_entries: list[DailyEntry],
    ) -> None:
        result = fmt.format_week(sample_daily_entries, "Dublin")
        assert "Dublin" in result
        assert "7-Day" in result

    def test_format_week_detail(
        self,
        fmt,
        sample_daily_entries: list[DailyEntry],
    ) -> None:
        result = fmt.format_week(sample_daily_entries, "Dublin", detail=True)
        # Detail mode shows per-day hourly tables
        assert "22/14" in result

    def test_format_compare(
        self,
        fmt,
        sample_current: CurrentWeather,
    ) -> None:
        result = fmt.format_compare([sample_current, sample_current])
        assert "Dublin" in result
        assert "Temp" in result
        assert "Humidity" in result

    def test_format_model_compare(
        self,
        fmt,
        sample_hourly_entries: list[HourlyEntry],
    ) -> None:
        model_data = {"gfs": sample_hourly_entries, "icon": sample_hourly_entries}
        result = fmt.format_model_compare(model_data, "Dublin")
        assert "Model Comparison" in result

    def test_negative_precipitation_probability(self, fmt) -> None:
        """History entries have precipitation_probability=-1."""
        from datetime import datetime
        entries = [HourlyEntry(
            time=datetime(2026, 5, 31, 10, 0),
            temperature=15.0,
            wind_speed=8.0,
            wind_direction=90,
            precipitation=0.0,
            precipitation_probability=-1,
        )]
        result = fmt.format_hourly(entries, "Test")
        # Should still render without error
        assert "Test" in result


# ── ASCII helper functions ─────────────────────────────────────────────


class TestAsciiHelpers:
    """Test internal helper functions in ascii formatter."""

    def test_prob_bar(self) -> None:
        from weather_meteo.formatters.ascii import _prob_bar
        assert _prob_bar(0) == ""
        assert len(_prob_bar(50)) == 5
        assert len(_prob_bar(100)) == 10

    def test_temp_color(self) -> None:
        from weather_meteo.formatters.ascii import _temp_color
        assert _temp_color(-5) == "bright_cyan"
        assert _temp_color(5) == "cyan"
        assert _temp_color(15) == "green"
        assert _temp_color(22) == "yellow"
        assert _temp_color(30) == "bright_red"
        assert _temp_color(35) == "red"

    def test_prob_color(self) -> None:
        from weather_meteo.formatters.ascii import _prob_color
        assert _prob_color(10) == "green"
        assert _prob_color(40) == "yellow"
        assert _prob_color(60) == "bright_red"
        assert _prob_color(80) == "red"

    def test_wind_color(self) -> None:
        from weather_meteo.formatters.ascii import _wind_color
        assert _wind_color(10) == "green"
        assert _wind_color(25) == "yellow"
        assert _wind_color(40) == "bright_red"
        assert _wind_color(60) == "red"

    def test_unit_suffix_metric(self) -> None:
        from weather_meteo.formatters.ascii import _unit_suffix
        t, w = _unit_suffix("metric")
        assert "C" in t
        assert "km" in w

    def test_unit_suffix_imperial(self) -> None:
        from weather_meteo.formatters.ascii import _unit_suffix
        t, w = _unit_suffix("imperial")
        assert "F" in t
        assert "mph" in w
