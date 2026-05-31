"""Tests for weather_meteo.config — Config, load/save round-trip."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from weather_meteo.config import (
    Config,
    LocationEntry,
    _build_config_header,
    load_config,
    save_config,
)


class TestConfigDefaults:
    """Config() has sensible defaults."""

    def test_default_values(self) -> None:
        cfg = Config()
        assert cfg.default_location == ""
        assert cfg.unit == "metric"
        assert cfg.format == "ascii"
        assert cfg.backend == "open-meteo"
        assert cfg.model == "best_match"
        assert cfg.locations == {}


class TestLocationEntry:
    """LocationEntry holds location data."""

    def test_basic_fields(self) -> None:
        loc = LocationEntry(lat=53.35, lon=-6.26, label="Dublin")
        assert loc.lat == 53.35
        assert loc.lon == -6.26
        assert loc.label == "Dublin"
        assert loc.model == ""

    def test_model_override(self) -> None:
        loc = LocationEntry(lat=0.0, lon=0.0, label="X", model="icon_seamless")
        assert loc.model == "icon_seamless"


class TestLoadSaveRoundTrip:
    """load_config/save_config round-trip via tmp_path."""

    def test_roundtrip(self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        config_dir = tmp_path / "weather-meteo"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("weather_meteo.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)

        original = Config(
            default_location="dublin",
            unit="metric",
            format="emoji",
            backend="open-meteo",
            model="icon_seamless",
            locations={
                "dublin": LocationEntry(lat=53.35, lon=-6.26, label="Dublin, Ireland"),
                "tokyo": LocationEntry(lat=35.68, lon=139.69, label="Tokyo, Japan", model="jma_seamless"),
            },
        )
        save_config(original)
        assert config_file.exists()

        loaded = load_config()
        assert loaded.default_location == original.default_location
        assert loaded.unit == original.unit
        assert loaded.format == original.format
        assert loaded.backend == original.backend
        assert loaded.model == original.model
        assert set(loaded.locations.keys()) == {"dublin", "tokyo"}
        assert loaded.locations["dublin"].lat == 53.35
        assert loaded.locations["tokyo"].model == "jma_seamless"

    def test_load_missing_file_returns_defaults(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config_file = tmp_path / "nonexistent" / "config.yaml"
        monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)
        cfg = load_config()
        assert cfg.default_location == ""
        assert cfg.unit == "metric"

    def test_load_empty_file(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config_file = tmp_path / "config.yaml"
        config_file.write_text("")
        monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)
        cfg = load_config()
        assert cfg.default_location == ""

    def test_save_creates_directory(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        config_dir = tmp_path / "deep" / "nested"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("weather_meteo.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)
        save_config(Config())
        assert config_dir.exists()

    def test_location_without_model(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Location with no model override should not write model key."""
        config_dir = tmp_path / "wm"
        config_file = config_dir / "config.yaml"
        monkeypatch.setattr("weather_meteo.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("weather_meteo.config.CONFIG_FILE", config_file)
        cfg = Config(locations={"home": LocationEntry(lat=1.0, lon=2.0, label="Home")})
        save_config(cfg)
        raw = yaml.safe_load(config_file.read_text().split("---")[-1] if "---" in config_file.read_text() else config_file.read_text())
        # model key should not appear for a location without model override
        assert "model" not in raw["locations"]["home"]


class TestBuildConfigHeader:
    """_build_config_header() produces a comment block."""

    def test_contains_model_ids(self) -> None:
        header = _build_config_header()
        assert "best_match" in header
        assert "ecmwf_ifs025" in header

    def test_all_lines_are_comments(self) -> None:
        header = _build_config_header()
        for line in header.strip().split("\n"):
            assert line.startswith("#")
