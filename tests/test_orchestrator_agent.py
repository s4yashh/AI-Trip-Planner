"""Orchestrator integration: one request through all three specialised agents.

These tests exercise the real agents - no static or fabricated results.
"""

from __future__ import annotations

import pytest

from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.poi_agent import POIRecommendationAgent
from models.schemas import ItineraryRequest, UserTripRequest


class FailingPOIAgent(POIRecommendationAgent):
    def run(self, input_data):
        raise RuntimeError("recommendation exploded")


class FailingItineraryAgent(ItineraryAgent):
    def run(self, input_data):
        raise RuntimeError("itinerary exploded")


class FailingBudgetAgent(BudgetAgent):
    def run(self, input_data):
        raise RuntimeError("budget exploded")


def test_full_multi_agent_workflow_produces_trip_plan():
    plan = OrchestratorAgent().run(
        UserTripRequest(
            destination="Rome",
            number_of_days=3,
            budget=700,
            interests=["Museum", "Food", "History"],
        )
    )
    assert plan.recommended_pois
    assert plan.itinerary.days
    assert plan.budget_analysis is not None
    assert plan.agent_execution_status.poi_recommendation is True
    assert plan.agent_execution_status.itinerary is True
    assert plan.agent_execution_status.budget is True
    assert plan.errors == []
    assert "Rome" in plan.trip_summary
    assert plan.budget_analysis.total_cost > 0
    assert "\u2713 POI Recommendation Agent" in plan.agent_execution_status.to_text()


def test_workflow_on_real_dataset(dataset_path, loaded_pois):
    assert len(loaded_pois) > 0
    plan = OrchestratorAgent(pois=loaded_pois).run(
        UserTripRequest(destination="Tokyo", number_of_days=2, interests=["Food"])
    )
    assert plan.recommended_pois
    assert plan.itinerary.planned_pois
    assert all(p.poi_id in plan.itinerary.planned_pois for p in plan.recommended_pois[:3])


def test_empty_poi_results_handled_gracefully():
    plan = OrchestratorAgent().run(
        UserTripRequest(destination="Atlantis", number_of_days=2, budget=500)
    )
    assert plan.recommended_pois == []
    assert plan.itinerary.days == []
    assert plan.budget_analysis is None
    assert plan.agent_execution_status.poi_recommendation is True
    assert plan.agent_execution_status.itinerary is False
    assert plan.agent_execution_status.budget is False
    assert plan.errors
    assert "\u2717 Itinerary Agent" in plan.agent_execution_status.to_text()


def test_invalid_user_request_raises():
    with pytest.raises(ValueError, match="UserTripRequest"):
        OrchestratorAgent().run("not a request")


def test_recommendation_failure_is_captured():
    plan = OrchestratorAgent(poi_agent=FailingPOIAgent([])).run(
        UserTripRequest(destination="Rome", number_of_days=2)
    )
    assert plan.agent_execution_status.poi_recommendation is False
    assert plan.agent_execution_status.itinerary is False
    assert plan.agent_execution_status.budget is False
    assert any("recommendation failed" in error for error in plan.errors)
    assert plan.recommended_pois == []


def test_itinerary_failure_is_captured():
    plan = OrchestratorAgent(itinerary_agent=FailingItineraryAgent()).run(
        UserTripRequest(destination="Rome", number_of_days=2)
    )
    assert plan.agent_execution_status.poi_recommendation is True
    assert plan.agent_execution_status.itinerary is False
    assert plan.agent_execution_status.budget is False
    assert any("Itinerary failed" in error for error in plan.errors)
    assert plan.budget_analysis is None


def test_budget_failure_is_captured():
    plan = OrchestratorAgent(budget_agent=FailingBudgetAgent()).run(
        UserTripRequest(destination="Rome", number_of_days=2)
    )
    assert plan.agent_execution_status.poi_recommendation is True
    assert plan.agent_execution_status.itinerary is True
    assert plan.agent_execution_status.budget is False
    assert any("Budget failed" in error for error in plan.errors)
    assert plan.budget_analysis is None


def test_top_k_limits_scheduled_pois():
    plan = OrchestratorAgent(top_k=2).run(
        UserTripRequest(destination="Paris", number_of_days=2)
    )
    assert len(plan.itinerary.planned_pois) <= 2


def test_specialised_agents_remain_independently_usable(loaded_pois):
    request = UserTripRequest(destination="Rome", number_of_days=2, interests=["museum"])
    recommendations = POIRecommendationAgent(loaded_pois).run(request)
    itinerary = ItineraryAgent().run(
        ItineraryRequest(number_of_days=2, ranked_pois=recommendations.results)
    )
    assert recommendations.results
    assert itinerary.days