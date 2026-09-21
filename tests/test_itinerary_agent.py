"""Itinerary agent scheduling behaviour."""

from __future__ import annotations

import pytest

from agents.itinerary_agent import ItineraryAgent
from models.schemas import ItineraryRequest


def _request(make_rec, durations, days=2):
    pois = [
        make_rec(poi_id=f"P{i}", name=f"POI {i}", visit_duration_hours=hours)
        for i, hours in enumerate(durations, start=1)
    ]
    return ItineraryRequest(number_of_days=days, ranked_pois=pois)


def test_single_day_schedules_all_pois(make_rec):
    request = _request(make_rec, [2.0, 2.0, 2.0], days=1)
    result = ItineraryAgent(daily_hours=8).run(request)
    assert result.days_used == 1
    assert len(result.planned_pois) == 3
    assert result.skipped_poi_ids == []


def test_multi_day_distributes_pois(make_rec):
    request = _request(make_rec, [3.0] * 5, days=3)
    result = ItineraryAgent(daily_hours=8).run(request)
    assert result.days_used == 3
    assert [len(day.items) for day in result.days] == [2, 2, 1]
    assert len(result.planned_pois) == 5


def test_insufficient_pois_produce_fewer_days(make_rec):
    request = _request(make_rec, [2.0, 2.0], days=4)
    result = ItineraryAgent(daily_hours=8).run(request)
    assert result.days_used == 1
    assert len(result.planned_pois) == 2


def test_duplicate_pois_scheduled_once(make_rec):
    first = make_rec(poi_id="P1", visit_duration_hours=2.0)
    request = ItineraryRequest(
        number_of_days=2,
        ranked_pois=[first, first, first.model_copy()],
    )
    result = ItineraryAgent().run(request)
    assert len(result.planned_pois) == 1


def test_daily_time_limit_not_exceeded(make_rec):
    request = _request(make_rec, [2.5, 2.5, 2.5, 2.5, 2.5], days=2)
    result = ItineraryAgent(daily_hours=6.0, gap_minutes=15).run(request)
    for day in result.days:
        total = sum(item.duration_hours for item in day.items)
        assert total <= 6.0 + 1e-9


def test_chronological_order_and_gap(make_rec):
    request = _request(make_rec, [2.0, 2.0], days=1)
    result = ItineraryAgent(daily_hours=8, gap_minutes=30).run(request)
    day = result.days[0]
    first, second = day.items
    assert first.start_time == "09:00"
    assert first.end_time == "11:00"
    assert second.start_time == "11:30"
    assert second.end_time == "13:30"


def test_higher_rank_placed_first_and_earlier(make_rec):
    high = make_rec(poi_id="P1", recommendation_score=0.9, visit_duration_hours=3.0)
    low = make_rec(poi_id="P2", recommendation_score=0.1, visit_duration_hours=3.0)
    result = ItineraryAgent(daily_hours=4).run(
        ItineraryRequest(number_of_days=2, ranked_pois=[high, low])
    )
    assert result.days[0].items[0].poi_id == "P1"
    assert result.days[1].items[0].poi_id == "P2"


def test_oversized_poi_is_reported_as_skipped(make_rec):
    big = make_rec(poi_id="BIG", visit_duration_hours=10.0)
    small = make_rec(poi_id="SMALL", visit_duration_hours=2.0)
    result = ItineraryAgent(daily_hours=8).run(
        ItineraryRequest(number_of_days=1, ranked_pois=[big, small])
    )
    assert "BIG" in result.skipped_poi_ids
    assert result.planned_pois == ["SMALL"]


def test_times_respect_start_hour_config(make_rec):
    request = _request(make_rec, [1.0], days=1)
    result = ItineraryAgent(day_start_hour=10).run(request)
    assert result.days[0].items[0].start_time == "10:00"


def test_invalid_input_raises():
    with pytest.raises(ValueError, match="ItineraryRequest"):
        ItineraryAgent().run("not a request")


def test_invalid_constructor_config():
    with pytest.raises(ValueError, match="daily_hours"):
        ItineraryAgent(daily_hours=0)
    with pytest.raises(ValueError, match="day_start_hour"):
        ItineraryAgent(day_start_hour=24)
    with pytest.raises(ValueError, match="gap_minutes"):
        ItineraryAgent(gap_minutes=-1)