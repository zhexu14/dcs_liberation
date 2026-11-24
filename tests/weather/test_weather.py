from datetime import date

from unittest.mock import MagicMock

import pytest

from game.settings import Settings
from game.theater.seasonalconditions import Season, SeasonalConditions, WeatherTypeChances
from game.timeofday import TimeOfDay
from game.weather.conditions import Conditions
from game.weather.weather import (
    ClearSkies,
    Cloudy,
    Raining,
    Thunderstorm,
    Weather,
    WeatherPreset,
    weather_preset_for,
)


def _make_seasonal_conditions() -> SeasonalConditions:
    """Create a minimal SeasonalConditions with equal weights for all weather types."""
    return SeasonalConditions(
        summer_avg_pressure=30.0,
        winter_avg_pressure=29.5,
        summer_avg_temperature=30.0,
        winter_avg_temperature=0.0,
        temperature_day_night_difference=10.0,
        high_avg_yearly_turbulence_per_10cm=2.0,
        low_avg_yearly_turbulence_per_10cm=0.5,
        solar_noon_turbulence_per_10cm=1.0,
        midnight_turbulence_per_10cm=0.2,
        weather_type_chances={
            Season.Winter: WeatherTypeChances(thunderstorm=0.25, raining=0.25, cloudy=0.25, clear_skies=0.25),
            Season.Spring: WeatherTypeChances(thunderstorm=0.25, raining=0.25, cloudy=0.25, clear_skies=0.25),
            Season.Summer: WeatherTypeChances(thunderstorm=0.25, raining=0.25, cloudy=0.25, clear_skies=0.25),
            Season.Fall: WeatherTypeChances(thunderstorm=0.25, raining=0.25, cloudy=0.25, clear_skies=0.25),
        },
    )


# ── WeatherPreset enum tests ────────────────────────────────────────────────


class TestWeatherPreset:
    def test_clear_skies_has_lowest_rank(self) -> None:
        assert WeatherPreset.CLEAR_SKIES.hierarchy_rank == 0

    def test_cloudy_rank(self) -> None:
        assert WeatherPreset.CLOUDY.hierarchy_rank == 1

    def test_raining_rank(self) -> None:
        assert WeatherPreset.RAINING.hierarchy_rank == 2

    def test_thunderstorms_has_highest_rank(self) -> None:
        assert WeatherPreset.THUNDERSTORMS.hierarchy_rank == 3

    def test_hierarchy_is_strictly_increasing(self) -> None:
        ranks = [p.hierarchy_rank for p in WeatherPreset]
        expected_ranks = [0, 1, 2, 3]
        assert ranks == expected_ranks


# ── weather_preset_for mapping tests ────────────────────────────────────────


class TestWeatherPresetFor:
    def test_clearskies_maps_to_clear_skies(self) -> None:
        assert weather_preset_for(ClearSkies) == WeatherPreset.CLEAR_SKIES

    def test_cloudy_maps_to_cloudy(self) -> None:
        assert weather_preset_for(Cloudy) == WeatherPreset.CLOUDY

    def test_raining_maps_to_raining(self) -> None:
        assert weather_preset_for(Raining) == WeatherPreset.RAINING

    def test_thunderstorm_maps_to_thunderstorms(self) -> None:
        assert weather_preset_for(Thunderstorm) == WeatherPreset.THUNDERSTORMS


# ── Conditions.generate_weather filtering tests ─────────────────────────────


class TestGenerateWeather:
    """Test that generate_weather filters weather types by the minimum preset."""

    def _generate(self, min_preset: WeatherPreset = WeatherPreset.THUNDERSTORMS) -> Weather:
        seasonal = _make_seasonal_conditions()
        return Conditions.generate_weather(
            seasonal, date.today(), TimeOfDay.Day, min_preset=min_preset
        )

    def test_default_allows_thunderstorms(self) -> None:
        """Default (THUNDERSTORMS) should allow all weather types."""
        for _ in range(100):
            result = self._generate()
            assert isinstance(result, (ClearSkies, Cloudy, Raining, Thunderstorm))

    def test_thunderstorms_minimum_allows_all(self) -> None:
        """THUNDERSTORMS as minimum should allow every weather type."""
        found_types: set[type[Weather]] = set()
        for _ in range(200):
            result = self._generate(min_preset=WeatherPreset.THUNDERSTORMS)
            found_types.add(type(result))
        assert found_types == {ClearSkies, Cloudy, Raining, Thunderstorm}

    def test_raining_excludes_thunderstorms(self) -> None:
        """RAINING as minimum should allow ClearSkies, Cloudy, Raining but not Thunderstorm."""
        found_types: set[type[Weather]] = set()
        for _ in range(200):
            result = self._generate(min_preset=WeatherPreset.RAINING)
            found_types.add(type(result))
        assert Thunderstorm not in found_types
        assert ClearSkies in found_types
        assert Cloudy in found_types
        assert Raining in found_types

    def test_cloudy_excludes_raining_and_thunderstorms(self) -> None:
        """CLOUDY as minimum should allow only ClearSkies and Cloudy."""
        found_types: set[type[Weather]] = set()
        for _ in range(200):
            result = self._generate(min_preset=WeatherPreset.CLOUDY)
            found_types.add(type(result))
        assert ClearSkies in found_types
        assert Cloudy in found_types
        assert Raining not in found_types
        assert Thunderstorm not in found_types

    def test_clear_skies_only_clear_skies(self) -> None:
        """CLEAR_SKIES as minimum should only produce ClearSkies."""
        for _ in range(50):
            result = self._generate(min_preset=WeatherPreset.CLEAR_SKIES)
            assert isinstance(result, ClearSkies)


# ── Settings integration test ───────────────────────────────────────────────


class TestSettingsWeatherMinimum:
    """Test that the weather_minimum setting is properly wired into Settings."""

    def test_settings_has_weather_minimum_attribute(self) -> None:
        settings = Settings()
        assert hasattr(settings, "weather_minimum")

    def test_settings_default_is_thunderstorms(self) -> None:
        settings = Settings()
        assert settings.weather_minimum == WeatherPreset.THUNDERSTORMS

    def test_settings_accepts_clear_skies(self) -> None:
        settings = Settings(weather_minimum=WeatherPreset.CLEAR_SKIES)
        assert settings.weather_minimum == WeatherPreset.CLEAR_SKIES

    def test_settings_accepts_cloudy(self) -> None:
        settings = Settings(weather_minimum=WeatherPreset.CLOUDY)
        assert settings.weather_minimum == WeatherPreset.CLOUDY

    def test_settings_accepts_raining(self) -> None:
        settings = Settings(weather_minimum=WeatherPreset.RAINING)
        assert settings.weather_minimum == WeatherPreset.RAINING

    def test_settings_accepts_thunderstorms(self) -> None:
        settings = Settings(weather_minimum=WeatherPreset.THUNDERSTORMS)
        assert settings.weather_minimum == WeatherPreset.THUNDERSTORMS
