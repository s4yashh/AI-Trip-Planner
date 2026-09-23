"""Weather agent interpretation behaviour (no network: fake service)."""

from __future__ import annotations

import pytest

from agents.weather_agent import WeatherAgent, setting_for_category
from models.schemas import UserTripRequest, WeatherRequest
from services.weather_service import WeatherServiceError


class FakeService:
    def __init__(self, days=None, error=None):
        self._days = days or []
        self._error = error

    def daily_forecast(self, latitude, longitude, start, days):
        if self._error:
            raise self._error
        return self._days[:days]


def _request(**overrides):
    base = {"destination": "Jaipur", "number_of_days": 2}
    base.update(overrides)
    return WeatherRequest(
        request=UserTripRequest(**base), latitude=26.92, longitude=75.82
    )


def _raw(condition, probability):
    return {
        "date": "2026-09-24",
        "temp_max_c": 30.0,
        "temp_min_c": 22.0,
        "precipitation_probability": probability,
        "weathercode": 61,
        "condition": condition,
        "wind_speed_kmh": 10.0,
    }


def test_rainy_day_avoids_outdoor():
    service = FakeService(days=[_raw("Rain", 80), _raw("Clear sky", 5)])
    report = WeatherAgent(service=service).run(_request())
    assert report.source == "live"
    assert report.days[0].avoid_outdoor is True
    assert report.days[1].avoid_outdoor is False
    assert "Day 1" in report.message


def test_clear_days_need_no_adjustment():
    service = FakeService(days=[_raw("Clear sky", 5), _raw("Partly cloudy", 10)])
    report = WeatherAgent(service=service).run(_request())
    assert all(day.avoid_outdoor is False for day in report.days)
    assert "No disruptive weather" in report.message


def test_provider_failure_returns_unavailable_report_not_crash():
    service = FakeService(error=WeatherServiceError("down"))
    report = WeatherAgent(service=service).run(_request())
    assert report.source == "unavailable"
    assert report.days == []
    assert "unavailable" in report.message.lower()


def test_missing_coordinates_returns_unavailable():
    request = WeatherRequest(
        request=UserTripRequest(destination="Jaipur", number_of_days=2)
    )
    report = WeatherAgent(service=FakeService()).run(request)
    assert report.source == "unavailable"


def test_start_date_aligns_forecast_days():
    seen = {}

    class Recording(FakeService):
        def daily_forecast(self, latitude, longitude, start, days):
            seen["start"] = start.isoformat()
            return self._days[:days]

    service = Recording(days=[_raw("Clear sky", 0)])
    WeatherAgent(service=service).run(_request(start_date="2026-10-01"))
    assert seen["start"] == "2026-10-01"


def test_setting_for_category_mapping():
    assert setting_for_category("Museum") == "indoor"
    assert setting_for_category("Landmark") == "outdoor"
    assert setting_for_category("mystery") == "outdoor"


def test_invalid_input_raises():
    with pytest.raises(ValueError, match="WeatherRequest"):
        WeatherAgent(service=FakeService()).run("not a request")
