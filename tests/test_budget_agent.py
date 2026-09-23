"""Budget agent estimation and budget-vs-request analysis."""

from __future__ import annotations

import pytest

from agents.budget_agent import DEFAULT_RATES, BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from models.schemas import BudgetRequest, ItineraryRequest, UserTripRequest


def _build_request(make_rec, days=2, budget=500.0, durations=(2.0, 2.0)):
    itinerary = ItineraryAgent(daily_hours=8).run(
        ItineraryRequest(
            number_of_days=days,
            ranked_pois=[
                make_rec(poi_id="P1", visit_duration_hours=durations[0], estimated_cost=40.0),
                make_rec(poi_id="P2", visit_duration_hours=durations[1], estimated_cost=25.0),
            ],
        )
    )
    user_request = UserTripRequest(
        destination="Test City", number_of_days=days, budget=budget
    )
    return BudgetRequest(request=user_request, itinerary=itinerary, pois=[])


def test_activities_derived_from_itinerary(make_rec):
    budget_request = _build_request(make_rec, days=1)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.activities == pytest.approx(65.0)


def test_accommodation_based_on_nights(make_rec):
    budget_request = _build_request(make_rec, days=3)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.accommodation == pytest.approx(
        2 * DEFAULT_RATES["accommodation_per_night"]
    )


def test_total_is_sum_of_categories(make_rec):
    budget_request = _build_request(make_rec, days=2)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.total_cost == pytest.approx(
        analysis.accommodation
        + analysis.transportation
        + analysis.food
        + analysis.activities
        + analysis.miscellaneous
    )


def test_within_budget(make_rec):
    budget_request = _build_request(make_rec, days=2, budget=2000.0)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.within_budget is True
    assert analysis.remaining_budget == pytest.approx(2000.0 - analysis.total_cost)
    assert analysis.suggestions == []


def test_over_budget_returns_savings_suggestions(make_rec):
    budget_request = _build_request(make_rec, days=2, budget=100.0)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.within_budget is False
    assert analysis.remaining_budget < 0
    assert len(analysis.suggestions) >= 2


def test_no_budget_set(make_rec):
    budget_request = _build_request(make_rec, days=2, budget=None)
    analysis = BudgetAgent().run(budget_request)
    assert analysis.within_budget is None
    assert analysis.remaining_budget is None
    assert any("budget" in suggestion.lower() for suggestion in analysis.suggestions)


def test_breakdown_is_transparent_and_sums_to_total(make_rec):
    budget_request = _build_request(make_rec, days=2)
    analysis = BudgetAgent().run(budget_request)
    categories = {item.category for item in analysis.breakdown}
    assert categories == {
        "Accommodation", "Transportation", "Food", "Activities", "Miscellaneous"
    }
    assert all(item.basis for item in analysis.breakdown)
    assert sum(item.amount for item in analysis.breakdown) == pytest.approx(analysis.total_cost)


def test_custom_rates_respected(make_rec):
    budget_request = _build_request(make_rec, days=2)
    analysis = BudgetAgent(rates={"accommodation_per_night": 250.0}).run(budget_request)
    assert analysis.accommodation == pytest.approx(250.0)


def test_invalid_input_raises():
    with pytest.raises(ValueError, match="BudgetRequest"):
        BudgetAgent().run("not a request")


def test_invalid_rates_rejected():
    with pytest.raises(ValueError, match="non-negative"):
        BudgetAgent(rates={"food_per_day": -10.0})