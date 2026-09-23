"""Places provider abstraction.

The default provider queries the Overpass API (OpenStreetMap, no API key)
for real nearby restaurants around a coordinate. The service only returns
raw listings; the RestaurantAgent ranks them with our own algorithm.

If the provider is unreachable, a :class:`PlacesServiceError` is raised and
the agent falls back to the local restaurant dataset (clearly labelled) or
a clear unavailable state — never fabricated listings.
"""

from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any, Callable

OVERPASS_URL = os.environ.get(
    "PLACES_API_URL", "https://overpass-api.de/api/interpreter"
)
PLACES_TIMEOUT_SECONDS = float(os.environ.get("PLACES_TIMEOUT_SECONDS", "12.0"))
DEFAULT_RESTAURANT_DATASET = (
    Path(__file__).resolve().parent.parent / "data" / "restaurants.csv"
)


class PlacesServiceError(Exception):
    """Raised when live restaurant listings cannot be retrieved."""


Fetcher = Callable[[str, dict[str, Any]], dict[str, Any]]


def _httpx_fetcher(url: str, payload: dict[str, Any]) -> dict[str, Any]:
    import httpx

    response = httpx.post(url, data=payload, timeout=PLACES_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def load_local_restaurants(
    path: str | Path, destination: str
) -> list[dict[str, Any]]:
    """Load curated local restaurant rows for a destination (fallback data)."""
    csv_path = Path(path)
    if not csv_path.is_file():
        return []
    target = destination.strip().lower()
    rows: list[dict[str, Any]] = []
    with csv_path.open(newline="", encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if (raw.get("destination") or "").strip().lower() != target:
                continue
            try:
                rows.append(
                    {
                        "restaurant_id": raw["restaurant_id"].strip(),
                        "name": raw["name"].strip(),
                        "cuisine": (raw.get("cuisine") or "").strip(),
                        "destination": raw.get("destination", "").strip(),
                        "rating": float(raw.get("rating") or 0.0),
                        "price_level": int(raw.get("price_level") or 2),
                        "latitude": float(raw.get("latitude") or 0.0),
                        "longitude": float(raw.get("longitude") or 0.0),
                        "source": "dataset",
                    }
                )
            except (KeyError, ValueError):
                continue
    return rows


class OverpassPlacesService:
    """Keyless Overpass-based restaurant listings with a small cache."""

    def __init__(
        self, endpoint: str = OVERPASS_URL, fetcher: Fetcher | None = None
    ) -> None:
        self._endpoint = endpoint
        self._fetcher = fetcher or _httpx_fetcher
        self._cache: dict[tuple[float, float, int, int], list[dict[str, Any]]] = {}

    def nearby_restaurants(
        self,
        latitude: float,
        longitude: float,
        radius_m: int = 3000,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Return raw live restaurant listings near a coordinate."""
        key = (round(latitude, 4), round(longitude, 4), radius_m, limit)
        if key in self._cache:
            return self._cache[key]
        query = (
            f'[out:json][timeout:25];node["amenity"="restaurant"]'
            f"(around:{radius_m},{latitude},{longitude});out {limit};"
        )
        try:
            payload = self._fetcher(self._endpoint, {"data": query})
            listings = [
                {
                    "restaurant_id": f"osm-{element.get('id')}",
                    "name": (element.get("tags") or {}).get("name", "Unnamed restaurant"),
                    "cuisine": (element.get("tags") or {}).get("cuisine", ""),
                    "rating": 0.0,
                    "price_level": 2,
                    "latitude": element.get("lat"),
                    "longitude": element.get("lon"),
                    "source": "live",
                }
                for element in payload.get("elements", [])
                if element.get("lat") is not None
            ][:limit]
        except Exception as exc:
            raise PlacesServiceError(
                f"places provider unreachable: {exc}"
            ) from exc
        self._cache[key] = listings
        return listings
