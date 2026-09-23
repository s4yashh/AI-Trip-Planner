"""Places provider behaviour (no network: injected fake fetcher)."""

from __future__ import annotations

import pytest

from services.places_service import (
    OverpassPlacesService,
    PlacesServiceError,
    load_local_restaurants,
)


def _overpass_payload():
    return {
        "elements": [
            {
                "id": 1,
                "lat": 26.92,
                "lon": 75.82,
                "tags": {"name": "Spice Court", "cuisine": "indian"},
            },
            {"id": 2, "lat": 26.93, "lon": 75.83, "tags": {}},
        ]
    }


def test_live_listings_are_returned_with_source():
    service = OverpassPlacesService(fetcher=lambda url, payload: _overpass_payload())
    listings = service.nearby_restaurants(26.92, 75.82)
    assert len(listings) == 2
    assert listings[0]["name"] == "Spice Court"
    assert listings[0]["source"] == "live"
    assert listings[1]["name"] == "Unnamed restaurant"


def test_provider_failure_raises_service_error():
    def broken(url, payload):
        raise RuntimeError("no network")

    service = OverpassPlacesService(fetcher=broken)
    with pytest.raises(PlacesServiceError):
        service.nearby_restaurants(26.92, 75.82)


def test_results_are_limited_and_cached():
    calls = []

    def counting(url, payload):
        calls.append(payload)
        return _overpass_payload()

    service = OverpassPlacesService(fetcher=counting)
    assert len(service.nearby_restaurants(26.92, 75.82, limit=1)) == 1
    service.nearby_restaurants(26.92, 75.82, limit=1)
    assert len(calls) == 1


def test_local_dataset_fallback_loads_destination_rows(tmp_path):
    csv_path = tmp_path / "restaurants.csv"
    csv_path.write_text(
        "restaurant_id,name,destination,cuisine,rating,review_count,"
        "price_level,latitude,longitude\n"
        "R1,Spice Court,Jaipur,indian,4.5,1200,2,26.92,75.82\n"
        "R2,Sushi Zen,Tokyo,japanese,4.7,800,3,35.68,139.76\n",
        encoding="utf-8",
    )
    rows = load_local_restaurants(csv_path, "jaipur")
    assert [row["restaurant_id"] for row in rows] == ["R1"]
    assert rows[0]["source"] == "dataset"


def test_local_dataset_missing_file_returns_empty(tmp_path):
    assert load_local_restaurants(tmp_path / "nope.csv", "Jaipur") == []
