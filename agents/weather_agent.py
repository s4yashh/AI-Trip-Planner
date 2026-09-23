"""Weather agent: interprets real forecast data into trip constraints.

The agent fetches raw forecast days from a weather provider service and
turns them into structured, itinerary-ready constraints (which trip days
should avoid outdoor visits). It never invents weather: when the provider
is unreachable it returns an explicit ``unavailable`` report so the
orchestrator can continue without weather adjustment.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from agents.base_agent import BaseAgent
from models.schemas import WeatherDayForecast, WeatherReport, WeatherRequest
from services.weather_service import OpenMeteoWeatherService, WeatherServiceError

#: Heuristic mapping from POI category to setting. The dataset has no
#: indoor/outdoor column, so this documented mapping is used for
#: weather-aware scheduling. Unknown categories default to "outdoor".
CATEGORY_SETTING: dict[str, str] = {
    "museum": "indoor",
    "entertainment": "indoor",
    "food": "indoor",
    "shopping": "indoor",
    "culture": "indoor",
    "landmark": "outdoor",
    "adventure": "outdoor",
    "outdoors": "outdoor",
}

#: Precipitation probability (%) at or above which outdoor visits are avoided.
AVOID_OUTDOOR_PRECIP_PROBABILITY = 50.0

#: Conditions that always trigger outdoor avoidance on that day.
AVOID_OUTDOOR_CONDITIONS = frozenset({"Rain", "Thunderstorm", "Snow"})


def setting_for_category(category: str) -> str:
    """Return 'indoor' or 'outdoor' for a POI category."""
    return CATEGORY_SETTING.get((category or "").strip().lower(), "outdoor")


class WeatherAgent(BaseAgent):
    """Produces a structured weather report for the requested trip days."""

    name = "weather-agent"

    def __init__(self, service: OpenMeteoWeatherService | None = None) -> None:
        self._service = service or OpenMeteoWeatherService()

    def run(self, input_data: Any) -> WeatherReport:
        if not isinstance(input_data, WeatherRequest):
            raise ValueError("input_data must be a WeatherRequest")
        request = input_data.request
        days = request.number_of_days
        start = self._start_date(request.start_date)

        if input_data.latitude is None or input_data.longitude is None:
            return WeatherReport(
                destination=request.destination,
                source="unavailable",
                message="Live weather unavailable: no coordinates for destination.",
            )
        try:
            raw_days = self._service.daily_forecast(
                input_data.latitude, input_data.longitude, start, days
            )
        except WeatherServiceError as exc:
            return WeatherReport(
                destination=request.destination,
                latitude=input_data.latitude,
                longitude=input_data.longitude,
                source="unavailable",
                message=f"Live weather unavailable ({exc}). "
                "Itinerary continues without weather adjustment.",
            )

        forecasts = [
            WeatherDayForecast(
                date=raw["date"],
                day_number=index + 1,
                temp_max_c=raw.get("temp_max_c"),
                temp_min_c=raw.get("temp_min_c"),
                precipitation_probability=raw.get("precipitation_probability"),
                condition=raw.get("condition") or "",
                wind_speed_kmh=raw.get("wind_speed_kmh"),
                avoid_outdoor=self._avoid_outdoor(raw),
            )
            for index, raw in enumerate(raw_days[:days])
        ]
        rainy = [day.day_number for day in forecasts if day.avoid_outdoor]
        if rainy:
            days_text = ", ".join(f"Day {number}" for number in rainy)
            message = (
                f"Rain expected on {days_text}: prefer indoor POIs "
                "and reschedule outdoor visits where possible."
            )
        else:
            message = "No disruptive weather expected during the trip."
        return WeatherReport(
            destination=request.destination,
            latitude=input_data.latitude,
            longitude=input_data.longitude,
            days=forecasts,
            source="live",
            message=message,
        )

    @staticmethod
    def _start_date(value: str | None) -> date:
        if value:
            try:
                return date.fromisoformat(value)
            except ValueError:
                pass
        return date.today()

    @staticmethod
    def _avoid_outdoor(raw: dict[str, Any]) -> bool:
        probability = raw.get("precipitation_probability") or 0.0
        try:
            wet = float(probability) >= AVOID_OUTDOOR_PRECIP_PROBABILITY
        except (TypeError, ValueError):
            wet = False
        return bool(wet or raw.get("condition") in AVOID_OUTDOOR_CONDITIONS)
