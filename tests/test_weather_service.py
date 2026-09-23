"""Weather provider behaviour (no network: injected fake fetcher)."""

from __future__ import annotations

from datetime import date

import pytest

from services.weather_service import (
    OpenMeteoWeatherService,
    WeatherServiceError,
    weather_code_to_condition,
)


def _payload():
    return {
        "daily": {
            "time": ["2026-09-24", "2026-09-25"],
            "temperature_2m_max": [31.0, 29.0],
            "temperature_2m_min": [22.0, 21.0],
            "precipitation_probability_max": [10, 80],
            "weathercode": [1, 61],
            "windspeed_10m_max": [12.0, 18.0],
        }
    }


def test_daily_forecast_parses_provider_response():
    service = OpenMeteoWeatherService(fetcher=lambda url, params: _payload())
    days = service.daily_forecast(26.92, 75.82, date(2026, 9, 24), 2)
    assert len(days) == 2
    assert days[0]["date"] == "2026-09-24"
    assert days[0]["temp_max_c"] == 31.0
    assert days[0]["condition"] == "Partly cloudy"
    assert days[1]["condition"] == "Rain"
    assert days[1]["precipitation_probability"] == 80


def test_provider_failure_raises_service_error():
    def broken(url, params):
        raise RuntimeError("no network")

    service = OpenMeteoWeatherService(fetcher=broken)
    with pytest.raises(WeatherServiceError):
        service.daily_forecast(26.92, 75.82, date(2026, 9, 24), 2)


def test_malformed_response_raises_service_error():
    service = OpenMeteoWeatherService(fetcher=lambda url, params: {"daily": {}})
    with pytest.raises(WeatherServiceError):
        service.daily_forecast(26.92, 75.82, date(2026, 9, 24), 2)


def test_repeated_calls_use_cache():
    calls = []

    def counting(url, params):
        calls.append(params)
        return _payload()

    service = OpenMeteoWeatherService(fetcher=counting)
    service.daily_forecast(26.92, 75.82, date(2026, 9, 24), 2)
    service.daily_forecast(26.92, 75.82, date(2026, 9, 24), 2)
    assert len(calls) == 1


def test_weather_code_mapping():
    assert weather_code_to_condition(0) == "Clear sky"
    assert weather_code_to_condition(61) == "Rain"
    assert weather_code_to_condition(95) == "Thunderstorm"
    assert weather_code_to_condition(None) == "Unknown"
