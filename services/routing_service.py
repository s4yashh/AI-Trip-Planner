"""Routing provider abstraction.

The default provider is the public OSRM demo server (no API key): it
returns real driving durations between coordinates. When the provider is
unreachable, the service falls back to a haversine-based estimate at a
documented city speed — and always labels which source was used so the
planner never pretends an estimate is live data.
"""

from __future__ import annotations

import math
import os
from typing import Any, Callable

OSRM_BASE_URL = os.environ.get(
    "ROUTES_API_URL", "https://router.project-osrm.org"
)
ROUTING_TIMEOUT_SECONDS = float(os.environ.get("ROUTING_TIMEOUT_SECONDS", "8.0"))
FALLBACK_CITY_SPEED_KMH = 30.0


class RoutingServiceError(Exception):
    """Raised when no travel time (live or estimated) can be produced."""


def haversine_km(
    origin: tuple[float, float], destination: tuple[float, float]
) -> float:
    """Great-circle distance in kilometres between (lat, lon) pairs."""
    lat1, lon1 = math.radians(origin[0]), math.radians(origin[1])
    lat2, lon2 = math.radians(destination[0]), math.radians(destination[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    inner = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    )
    return 2 * 6371.0 * math.asin(math.sqrt(inner))


Fetcher = Callable[[str], dict[str, Any]]


def _httpx_fetcher(url: str) -> dict[str, Any]:
    import httpx

    response = httpx.get(url, timeout=ROUTING_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


class RoutingService:
    """OSRM-backed travel times with a labelled haversine fallback + cache."""

    def __init__(
        self, base_url: str = OSRM_BASE_URL, fetcher: Fetcher | None = None
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._fetcher = fetcher or _httpx_fetcher
        self._cache: dict[tuple[float, float, float, float], tuple[float, str]] = {}

    def travel_minutes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> tuple[float, str]:
        """Return (minutes, source) where source is 'live' or 'estimate'."""
        key = (
            round(origin[0], 5),
            round(origin[1], 5),
            round(destination[0], 5),
            round(destination[1], 5),
        )
        if key in self._cache:
            return self._cache[key]
        minutes, source = self._live_minutes(origin, destination)
        if minutes is None:
            minutes = (
                haversine_km(origin, destination) / FALLBACK_CITY_SPEED_KMH * 60.0
            )
            source = "estimate"
        result = (round(max(minutes, 1.0), 1), source)
        self._cache[key] = result
        return result

    def pairwise_minutes(
        self, points: list[tuple[str, float, float]]
    ) -> tuple[dict[str, float], str]:
        """Travel minutes for every ordered pair, keyed 'idA>idB'.

        Returns the mapping plus the overall source: 'live' only when every
        leg came from the routing API, otherwise 'estimate'.
        """
        legs: dict[str, float] = {}
        overall = "live"
        for from_id, from_lat, from_lon in points:
            for to_id, to_lat, to_lon in points:
                if from_id == to_id:
                    continue
                minutes, source = self.travel_minutes(
                    (from_lat, from_lon), (to_lat, to_lon)
                )
                legs[f"{from_id}>{to_id}"] = minutes
                if source != "live":
                    overall = "estimate"
        return legs, overall

    def _live_minutes(
        self, origin: tuple[float, float], destination: tuple[float, float]
    ) -> tuple[float | None, str]:
        url = (
            f"{self._base_url}/route/v1/driving/"
            f"{origin[1]},{origin[0]};{destination[1]},{destination[0]}"
            "?overview=false"
        )
        try:
            payload = self._fetcher(url)
            seconds = payload["routes"][0]["duration"]
            return float(seconds) / 60.0, "live"
        except Exception:
            return None, "estimate"
