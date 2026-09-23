"""Validation engine behaviour: every check and the pass-through case."""

from __future__ import annotations

from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from models.schemas import (
    BudgetAnalysis,
    BudgetRequest,
    ItineraryDay,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
    Restaurant,
    RestaurantList,
    UserTripRequest,
    WeatherDayForecast,
    WeatherReport,
)
from validation.trip_validator import MAX_REPLAN_ATTEMPTS, TripValidator


def _request(**overrides):
    base = {"destination": "Test City", "number_of_days": 2, "budget": 2000.0}
    base.update(overrides)
    return UserTripRequest(**base)


def _pois(make_poi, ids=("P1", "P2")):
    return [make_poi(poi_id=pid, destination="Test City") for pid in ids]


def _recs(make_rec, ids=("P1", "P2"), **overrides):
    return [make_rec(poi_id=pid, **overrides) for pid in ids]


def _plan(make_rec, days=2, budget=2000.0):
    itinerary = ItineraryAgent().run(
        ItineraryRequest(number_of_days=days, ranked_pois=_recs(make_rec))
    )
    analysis = BudgetAgent().run(
        BudgetRequest(
            request=_request(number_of_days=days, budget=budget),
            itinerary=itinerary,
        )
    )
    return itinerary, analysis


def _codes(report):
    return {violation.code for violation in report.violations}


def test_valid_plan_passes(make_poi, make_rec):
    request = _request()
    itinerary, budget = _plan(make_rec)
    report = TripValidator().validate(
        request, _recs(make_rec), itinerary, budget, pois=_pois(make_poi)
    )
    assert report.passed is True
    assert report.violations == []
    assert report.max_attempts == MAX_REPLAN_ATTEMPTS >= 1


def test_day_count_violation(make_poi, make_rec):
    report = TripValidator().validate(
        _request(),
        _recs(make_rec),
        ItineraryResponse(days=[ItineraryDay(day_number=1, items=[])]),
        None,
        pois=_pois(make_poi),
    )
    assert report.passed is False
    assert "day_count" in _codes(report)


def test_duplicate_pois_rejected(make_poi, make_rec):
    item = ItineraryItem(
        poi_id="P1",
        name="Place",
        start_time="09:00",
        end_time="11:00",
        duration_hours=2.0,
        estimated_cost=10.0,
    )
    itinerary = ItineraryResponse(
        days=[
            ItineraryDay(day_number=1, items=[item]),
            ItineraryDay(day_number=2, items=[item]),
        ]
    )
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, None, pois=_pois(make_poi)
    )
    assert "duplicate_poi" in _codes(report)


def test_unknown_poi_rejected(make_poi, make_rec):
    item = ItineraryItem(
        poi_id="GHOST",
        name="Ghost",
        start_time="09:00",
        end_time="10:00",
        duration_hours=1.0,
        estimated_cost=0.0,
    )
    itinerary = ItineraryResponse(
        days=[
            ItineraryDay(day_number=1, items=[item]),
            ItineraryDay(day_number=2, items=[]),
        ]
    )
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, None, pois=_pois(make_poi)
    )
    assert "unknown_poi" in _codes(report)


def test_invalid_poi_destination_rejected(make_poi, make_rec):
    pois = [make_poi(poi_id="P1", destination="Paris")]
    report = TripValidator().validate(
        UserTripRequest(destination="Rome", number_of_days=1),
        _recs(make_rec, ids=("P1",)),
        ItineraryResponse(days=[ItineraryDay(day_number=1, items=[])]),
        None,
        pois=pois,
    )
    assert "destination_mismatch" in _codes(report)


def test_time_overlap_rejected(make_poi, make_rec):
    items = [
        ItineraryItem(
            poi_id="P1", name="A", start_time="09:00", end_time="11:00",
            duration_hours=2.0, estimated_cost=0.0,
        ),
        ItineraryItem(
            poi_id="P2", name="B", start_time="10:30", end_time="12:00",
            duration_hours=1.5, estimated_cost=0.0,
        ),
    ]
    itinerary = ItineraryResponse(
        days=[
            ItineraryDay(day_number=1, items=items),
            ItineraryDay(day_number=2, items=[]),
        ]
    )
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, None, pois=_pois(make_poi)
    )
    assert "time_overlap" in _codes(report)


def test_duration_mismatch_rejected(make_poi, make_rec):
    item = ItineraryItem(
        poi_id="P1", name="A", start_time="09:00", end_time="11:00",
        duration_hours=5.0, estimated_cost=0.0,
    )
    itinerary = ItineraryResponse(
        days=[
            ItineraryDay(day_number=1, items=[item]),
            ItineraryDay(day_number=2, items=[]),
        ]
    )
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, None, pois=_pois(make_poi)
    )
    assert "duration_mismatch" in _codes(report)


def test_opening_hours_respected_when_available(make_poi, make_rec):
    recs = _recs(make_rec, ids=("P1",), open_hour=10)
    item = ItineraryItem(
        poi_id="P1", name="A", start_time="09:00", end_time="10:00",
        duration_hours=1.0, estimated_cost=0.0,
    )
    itinerary = ItineraryResponse(
        days=[ItineraryDay(day_number=1, items=[item])]
    )
    report = TripValidator().validate(
        UserTripRequest(destination="Test City", number_of_days=1),
        recs,
        itinerary,
        None,
        pois=_pois(make_poi, ids=("P1",)),
    )
    assert "opening_hours" in _codes(report)


def test_travel_gap_violation(make_poi, make_rec):
    items = [
        ItineraryItem(
            poi_id="P1", name="A", start_time="09:00", end_time="10:00",
            duration_hours=1.0, estimated_cost=0.0,
            travel_minutes_to_next=60.0, travel_source="live",
        ),
        ItineraryItem(
            poi_id="P2", name="B", start_time="10:15", end_time="11:00",
            duration_hours=0.75, estimated_cost=0.0,
        ),
    ]
    itinerary = ItineraryResponse(
        days=[
            ItineraryDay(day_number=1, items=items),
            ItineraryDay(day_number=2, items=[]),
        ]
    )
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, None, pois=_pois(make_poi)
    )
    assert "travel_gap" in _codes(report)


def test_over_budget_rejected(make_poi, make_rec):
    request = _request(budget=10.0)
    itinerary, budget = _plan(make_rec, budget=10.0)
    report = TripValidator().validate(
        request, _recs(make_rec), itinerary, budget, pois=_pois(make_poi)
    )
    assert "over_budget" in _codes(report)


def test_budget_components_must_sum_exactly(make_poi, make_rec):
    budget = BudgetAnalysis(
        accommodation=10.0,
        transportation=10.0,
        food=10.0,
        activities=10.0,
        miscellaneous=10.0,
        total_cost=999.0,
        user_budget=2000.0,
        within_budget=True,
        remaining_budget=1001.0,
        suggestions=[],
        breakdown=[],
    )
    itinerary, _ = _plan(make_rec)
    report = TripValidator().validate(
        _request(), _recs(make_rec), itinerary, budget, pois=_pois(make_poi)
    )
    assert "budget_sum" in _codes(report)


def test_restaurant_over_budget_rejected(make_poi, make_rec):
    itinerary, budget = _plan(make_rec)
    restaurants = RestaurantList(
        request=_request(),
        results=[
            Restaurant(
                restaurant_id="R1",
                name="Luxury",
                cuisine="french",
                rating=4.9,
                price_level=3,
                restaurant_score=0.9,
                reason="",
                source="dataset",
            )
        ],
        source="dataset",
    )
    report = TripValidator().validate(
        _request(),
        _recs(make_rec),
        itinerary,
        budget,
        restaurants=restaurants,
        daily_food_budget=5.0,
        pois=_pois(make_poi),
    )
    assert "restaurant_over_budget" in _codes(report)


def test_weather_violation_when_outdoor_on_rainy_day(make_poi, make_rec):
    itinerary, budget = _plan(make_rec)
    weather = WeatherReport(
        destination="Test City",
        days=[
            WeatherDayForecast(
                date="2026-09-24", day_number=1, condition="Rain",
                avoid_outdoor=True,
            ),
            WeatherDayForecast(
                date="2026-09-25", day_number=2, condition="Clear sky",
                avoid_outdoor=False,
            ),
        ],
        source="live",
    )
    recs = _recs(make_rec, setting="outdoor")
    report = TripValidator().validate(
        _request(), recs, itinerary, budget, weather=weather, pois=_pois(make_poi)
    )
    assert "weather_violation" in _codes(report)


def test_weather_skipped_when_unavailable(make_poi, make_rec):
    itinerary, budget = _plan(make_rec)
    weather = WeatherReport(destination="Test City", source="unavailable")
    report = TripValidator().validate(
        _request(),
        _recs(make_rec),
        itinerary,
        budget,
        weather=weather,
        pois=_pois(make_poi),
    )
    assert "weather_violation" not in _codes(report)
