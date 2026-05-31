"""Tests for weather_meteo.location — alias resolution (no HTTP)."""

from __future__ import annotations

import click
import pytest

from weather_meteo.config import Config, LocationEntry
from weather_meteo.location import resolve_location


class TestResolveLocation:
    """resolve_location() looks up aliases without network calls."""

    def test_known_alias(self, sample_config: Config) -> None:
        loc = resolve_location("dublin", sample_config)
        assert loc.lat == 53.35
        assert loc.label == "Dublin, Leinster, Ireland"

    def test_default_location(self, sample_config: Config) -> None:
        loc = resolve_location(None, sample_config)
        assert loc.lat == 53.35

    def test_no_location_raises(self) -> None:
        cfg = Config()  # no default, no locations
        with pytest.raises(click.ClickException, match="No location specified"):
            resolve_location(None, cfg)

    def test_unknown_name_calls_geocode(
        self,
        sample_config: Config,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Unknown names fall through to _geocode; we mock it."""
        fake_loc = LocationEntry(lat=48.85, lon=2.35, label="Paris, France")
        monkeypatch.setattr(
            "weather_meteo.location._geocode",
            lambda name: fake_loc,
        )
        loc = resolve_location("paris", sample_config)
        assert loc.label == "Paris, France"
