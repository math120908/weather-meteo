"""Tests for weather_meteo.models — pure functions and data structures."""

from __future__ import annotations

import pytest

from weather_meteo.models import (
    FORECAST_MODELS,
    RAIN_SPARK,
    WIND_ARROWS,
    CurrentWeather,
    DailyEntry,
    HourlyEntry,
    rain_spark_char,
    weather_description,
    wind_arrow,
)


class TestWindArrow:
    """wind_arrow() maps degrees to 8 compass arrows."""

    @pytest.mark.parametrize(
        "degrees, expected",
        [
            (0, "↑"),      # N
            (45, "↗"),     # NE
            (90, "→"),     # E
            (135, "↘"),    # SE
            (180, "↓"),    # S
            (225, "↙"),    # SW
            (270, "←"),    # W
            (315, "↖"),    # NW
            (360, "↑"),    # wrap to N
        ],
    )
    def test_cardinal_directions(self, degrees: int, expected: str) -> None:
        assert wind_arrow(degrees) == expected

    def test_intermediate_rounds_down(self) -> None:
        # 20 degrees rounds to 0 (N)
        assert wind_arrow(20) == "↑"

    def test_intermediate_rounds_up(self) -> None:
        # 25 degrees rounds to 45 (NE)
        assert wind_arrow(25) == "↗"

    def test_large_degrees(self) -> None:
        # Modulo wrapping for values > 360
        assert wind_arrow(405) == "↗"


class TestRainSparkChar:
    """rain_spark_char() maps probability to spark bar characters."""

    @pytest.mark.parametrize(
        "prob, expected_index",
        [
            (0, 0),
            (10, 0),
            (11, 1),
            (25, 1),
            (26, 2),
            (40, 2),
            (41, 3),
            (55, 3),
            (56, 4),
            (75, 4),
            (76, 5),
            (100, 5),
        ],
    )
    def test_probability_buckets(self, prob: int, expected_index: int) -> None:
        assert rain_spark_char(prob) == RAIN_SPARK[expected_index]


class TestWeatherDescription:
    """weather_description() returns WMO code descriptions."""

    def test_known_code(self) -> None:
        assert weather_description(0) == "Clear sky"
        assert weather_description(95) == "Thunderstorm"

    def test_unknown_code(self) -> None:
        assert weather_description(999) == "Unknown (999)"

    def test_all_known_codes_return_strings(self) -> None:
        from weather_meteo.models import WMO_DESCRIPTIONS
        for code in WMO_DESCRIPTIONS:
            desc = weather_description(code)
            assert isinstance(desc, str)
            assert "Unknown" not in desc


class TestForecastModels:
    """FORECAST_MODELS is a non-empty list of (id, description) tuples."""

    def test_not_empty(self) -> None:
        assert len(FORECAST_MODELS) > 0

    def test_tuple_format(self) -> None:
        for model_id, desc in FORECAST_MODELS:
            assert isinstance(model_id, str)
            assert isinstance(desc, str)

    def test_best_match_is_first(self) -> None:
        assert FORECAST_MODELS[0][0] == "best_match"
