"""Restaurant agent ranking behaviour (no network: fake service)."""

from __future__ import annotations

import pytest

from agents.restaurant_agent import RestaurantAgent
from models.schemas import RestaurantRequest, UserTripRequest
from services.places_service import PlacesServiceError


def _request(**overrides):
    base = {
        "destination": "Jaipur",
        "number_of_days": 2,
        "interests": ["food"],
    }
    base.update(overrides)
    payload = {
        "request": UserTripRequest(**base),
        "latitude": 26.92,
        "longitude": 75.82,
        "daily_food_budget": 20.0,
    }
    return RestaurantRequest(**payload)


def _listing(name, cuisine, rating, price, lat=26.92, lon=75.82, source="live"):
    return {
        "restaurant_id": name,
        "name": name,
        "cuisine": cuisine,
        "rating": rating,
        "price_level": price,
        "latitude": lat,
        "longitude": lon,
        "source": source,
    }


class FakeService:
    def __init__(self, listings=None, error=None):
        self._listings = listings or []
        self._error = error

    def nearby_restaurants(self, latitude, longitude, radius_m=3000, limit=20):
        if self._error:
            raise self._error
        return self._listings


def test_live_listings_are_ranked_by_own_algorithm():
    listings = [
        _listing("Far Far Away", "mexican", 3.0, 3, lat=27.5, lon=76.5),
        _listing("Spice Court", "indian", 4.5, 2),
    ]
    agent = RestaurantAgent(service=FakeService(listings=listings))
    result = agent.run(_request())
    assert result.source == "live"
    assert result.results[0].name == "Spice Court"
    assert all(0.0 <= item.restaurant_score <= 1.0 for item in result.results)


def test_cuisine_match_outranks_plain_rating():
    listings = [
        _listing("Casa Verde", "mexican", 4.4, 1),
        _listing("Spice Court", "indian", 4.3, 1),
    ]
    agent = RestaurantAgent(service=FakeService(listings=listings))
    result = agent.run(_request())
    assert result.results[0].name == "Spice Court"


def test_budget_fit_prefers_affordable():
    listings = [
        _listing("Luxury Dine", "indian", 4.9, 3),
        _listing("Budget Bite", "indian", 4.2, 1),
    ]
    agent = RestaurantAgent(service=FakeService(listings=listings))
    tight = agent.run(_request(daily_food_budget=8.0))
    assert tight.results[0].name == "Budget Bite"


def test_weights_are_configurable_not_hardcoded():
    agent = RestaurantAgent(
        service=FakeService(),
        weights={
            "cuisine_similarity": 0.1,
            "rating": 0.7,
            "budget_fit": 0.1,
            "distance": 0.1,
        },
    )
    assert agent._weights["rating"] == 0.7


def test_invalid_weights_rejected():
    with pytest.raises(ValueError, match="sum to 1.0"):
        RestaurantAgent(
            service=FakeService(),
            weights={
                "cuisine_similarity": 0.2,
                "rating": 0.2,
                "budget_fit": 0.2,
                "distance": 0.2,
            },
        )


def test_provider_failure_uses_dataset_fallback(tmp_path):
    csv_path = tmp_path / "restaurants.csv"
    csv_path.write_text(
        "restaurant_id,name,destination,cuisine,rating,review_count,"
        "price_level,latitude,longitude\n"
        "R1,Spice Court,Jaipur,indian,4.5,1200,2,26.92,75.82\n",
        encoding="utf-8",
    )
    agent = RestaurantAgent(
        service=FakeService(error=PlacesServiceError("down")),
        dataset_path=str(csv_path),
    )
    result = agent.run(_request())
    assert result.source == "dataset"
    assert [item.name for item in result.results] == ["Spice Court"]
    assert "dataset" in result.message.lower()


def test_total_outage_returns_unavailable_state(tmp_path):
    agent = RestaurantAgent(
        service=FakeService(error=PlacesServiceError("down")),
        dataset_path=str(tmp_path / "missing.csv"),
    )
    result = agent.run(_request())
    assert result.source == "unavailable"
    assert result.results == []


def test_invalid_input_raises():
    with pytest.raises(ValueError, match="RestaurantRequest"):
        RestaurantAgent(service=FakeService()).run("not a request")
