"""Pydantic model construction and validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.schemas import POI, UserTripRequest

VALID_POI = {
    "poi_id": "POI999",
    "name": "Test Museum",
    "destination": "Test City",
    "category": "Museum",
    "description": "A test point of interest.",
    "rating": 4.5,
    "review_count": 1200,
    "visit_duration_hours": 2.0,
    "estimated_cost": 15.0,
    "latitude": 51.50,
    "longitude": -0.12,
}


def test_poi_object_can_be_created():
    poi = POI(**VALID_POI)
    assert poi.poi_id == "POI999"
    assert poi.rating == 4.5
    assert poi.review_count == 1200


def test_poi_rejects_out_of_range_rating():
    with pytest.raises(ValidationError):
        POI(**{**VALID_POI, "rating": 5.5})


def test_poi_rejects_negative_cost():
    with pytest.raises(ValidationError):
        POI(**{**VALID_POI, "estimated_cost": -1.0})


def test_poi_rejects_invalid_latitude():
    with pytest.raises(ValidationError):
        POI(**{**VALID_POI, "latitude": 91.0})


def test_poi_rejects_empty_description():
    with pytest.raises(ValidationError):
        POI(**{**VALID_POI, "description": "   "})


def test_poi_rank_score_calculated(loaded_pois):
    top = max(loaded_pois, key=lambda p: p.rank_score)
    assert top.rank_score >= 0


def test_poi_loaded_from_dataset_match_schema(loaded_pois):
    for poi in loaded_pois:
        assert isinstance(poi, POI)


def test_user_trip_request_valid():
    request = UserTripRequest(
        destination="Tokyo", number_of_days=5, budget=1200.0, interests=["Food", "Museum"]
    )
    assert request.destination == "Tokyo"
    assert request.number_of_days == 5


def test_user_trip_request_defaults_interests():
    request = UserTripRequest(destination="Rome", number_of_days=3)
    assert request.interests == []
    assert request.budget is None


def test_user_trip_request_rejects_zero_days():
    with pytest.raises(ValidationError):
        UserTripRequest(destination="Rome", number_of_days=0)


def test_user_trip_request_rejects_empty_destination():
    with pytest.raises(ValidationError):
        UserTripRequest(destination="   ", number_of_days=2)


def test_user_trip_request_normalises_interests():
    request = UserTripRequest(
        destination="Paris", number_of_days=2, interests=["  FOOD ", "Museum", ""]
    )
    assert request.interests == ["food", "museum"]


def test_user_trip_request_rejects_negative_budget():
    with pytest.raises(ValidationError):
        UserTripRequest(destination="Paris", number_of_days=2, budget=-5.0)