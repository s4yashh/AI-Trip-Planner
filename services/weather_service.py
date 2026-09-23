"""Weather provider abstraction.

The default provider is Open-Meteo (https://open-meteo.com), which needs
no API key: it returns real forecast data (temperature, WMO weather code,
precipitation probability, wind). The service only fetches raw data; the
WeatherAgent interprets it into trip constraints.

If the provider is unreachable, a :class:`WeatherServiceError` is raised
and callers are expected to degrade gracefully (never crash the planner).
"""

from __future__ import annotations

import os
from datetime import date, timedelta
from typing import Any, Callable

OPEN_METEO_URL = os.environ.get(
    "WEATHER_API_URL", "https://api.open-meteo.com/v1/forecast"
)
WEATHER_TIMEOUT_SECONDS = float(os.environ.get("WEATHER_TIMEOUT_SECONDS", "8.0"))


class WeatherServiceError(Exception):
    """Raised when live weather data cannot be retrieved."""


def weather_code_to_condition(code: int | None) -> str:
    """Map a WMO weather code to a short human-readable condition."""
    if code is None:
        return "Unknown"
    if code == 0:
        return "Clear sky"
    if code in (1, 2, 3):
        return "Partly cloudy"
    if code in (45, 48):
        return "Fog"
    if code in (51, 53, 55, 56, 57):
        return "Drizzle"
    if code in (61, 63, 65, 66, 67, 80, 81, 82):
        return "Rain"
    if code in (71, 73, 75, 77, 85, 86):
        return "Snow"
    if code in (95, 96, 99):
        return "Thunderstorm"
    return "Cloudy"


Fetcher = Callable[[str, dict[str, Any]], dict[str, Any]]


def _httpx_fetcher(url: str, params: dict[str, Any]) -> dict[str, Any]:
    import httpx

    response = httpx.get(url, params=params, timeout=WEATHER_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


class OpenMeteoWeatherService:
    """Keyless Open-Meteo forecast provider with a small in-memory cache."""

    def __init__(
        self,
        base_url: str = OPEN_METEO_URL,
        fetcher: Fetcher | None = None,
    ) -> None:
        self._base_url = base_url
        self._fetcher = fetcher or _httpx_fetcher
        self._cache: dict[tuple[float, float, str, int], list[dict[str, Any]]] = {}

    def daily_forecast(
        self, latitude: float, longitude: float, start: date, days: int
    ) -> list[dict[str, Any]]:
        """Return one raw forecast dict per day starting at ``start``.

        Each dict has keys: date, temp_max_c, temp_min_c,
        precipitation_probability, weathercode, condition, wind_speed_kmh.
        """
        key = (round(latitude, 4), round(longitude, 4), start.isoformat(), days)
        if key in self._cache:
            return self._cache[key]
        try:
            payload = self._fetcher(
                self._base_url,
                {
                    "latitude": latitude,
                    "longitude": longitude,
                    "daily": (
                        "temperature_2m_max,temperature_2m_min,"
                        "precipitation_probability_max,weathercode,"
                        "windspeed_10m_max"
                    ),
                    "timezone": "auto",
                    "start_date": start.isoformat(),
                    "end_date": (start + timedelta(days=max(days - 1, 0))).isoformat(),
                },
            )
        except Exception as exc:
            raise WeatherServiceError(f"weather provider unreachable: {exc}") from exc
        try:
            daily = payload["daily"]
            result = [
                {
                    "date": day,
                    "temp_max_c": daily["temperature_2m_max"][i],
                    "temp_min_c": daily["temperature_2m_min"][i],
                    "precipitation_probability": daily[
                        "precipitation_probability_max"
                    ][i],
                    "weathercode": daily["weathercode"][i],
                    "condition": weather_code_to_condition(
                        daily["weathercode"][i]
                    ),
                    "wind_speed_kmh": daily["windspeed_10m_max"][i],
                }
                for i, day in enumerate(daily["time"])
            ]
        except (KeyError, IndexError, TypeError) as exc:
            raise WeatherServiceError(
                f"unexpected weather provider response: {exc}"
            ) from exc
        self._cache[key] = result
        return result
