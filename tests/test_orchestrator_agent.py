"""Orchestrator integration: one request through all specialised agents.

These tests exercise the real agents - no static or fabricated results.
External providers are offline in tests (see conftest): weather returns an
unavailable report, restaurants fall back to the local dataset and routing
uses labelled haversine estimates.
"""

from __future__ import annotations

import pytest

from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.orchestrator_agent import (
    NO_FEASIBLE_ITINERARY_MESSAGE,
    OrchestratorAgent,
)
from agents.poi_agent import POIRecommendationAgent
from agents.restaurant_agent import RestaurantAgent
from agents.weather_agent import WeatherAgent
from models.schemas import (
    ItineraryRequest,
    RestaurantList,
    UserTripRequest,
    WeatherReport,
)
from services.places_service import PlacesServiceError
from services.weather_service import WeatherServiceError


class FailingPOIAgent(POIRecommendationAgent):
    def run(self, input_data):
        raise RuntimeError("recommendation exploded")


class FailingItineraryAgent(ItineraryAgent):
    def run(self, input_data):
        raise RuntimeError("itinerary exploded")


class FailingBudgetAgent(BudgetAgent):
    def run(self, input_data):
        raise RuntimeError("budget exploded")


class FailingWeatherAgent(WeatherAgent):
    def run(self, input_data):
        raise RuntimeError("weather exploded")


class FailingRestaurantAgent(RestaurantAgent):
    def run(self, input_data):
        raise RuntimeError("restaurant exploded")


class ExplodingWeatherService:
    def daily_forecast(self, latitude, longitude, start, days):
        raise WeatherServiceError("storm took the API down")


class ExplodingPlacesService:
    def nearby_restaurants(self, latitude, longitude, radius_m=3000, limit=20):
        raise PlacesServiceError("places down")


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


def test_budget_pruning_triggers_replanning_within_limit():
    plan = OrchestratorAgent().run(
        UserTripRequest(
            destination="Paris", number_of_days=2, budget=100.0, interests=[]
        )
    )
    assert plan.budget_analysis is not None
    assert plan.budget_analysis.total_cost <= 100.0
    assert plan.budget_analysis.within_budget is True
    assert plan.validation_report is not None
    assert plan.validation_report.passed is True
    assert plan.validation_report.attempts >= 1
    assert plan.validation_report.attempts <= plan.validation_report.max_attempts
    assert any("removed" in note for note in plan.validation_report.notes)
    assert len(plan.itinerary.planned_pois) < len(plan.recommended_pois)


def test_infeasible_budget_returns_exact_message():
    plan = OrchestratorAgent().run(
        UserTripRequest(
            destination="Jaipur", number_of_days=3, budget=1.0, interests=["History"]
        )
    )
    assert plan.trip_summary == NO_FEASIBLE_ITINERARY_MESSAGE
    assert NO_FEASIBLE_ITINERARY_MESSAGE in plan.errors
    assert plan.recommended_pois == []
    assert plan.itinerary.days == []
    assert plan.budget_analysis is None


def test_replanning_has_maximum_attempt_limit():
    plan = OrchestratorAgent(max_replan_attempts=1).run(
        UserTripRequest(
            destination="Jaipur", number_of_days=3, budget=1.0, interests=["History"]
        )
    )
    assert plan.validation_report is not None
    assert plan.validation_report.attempts == 1
    assert NO_FEASIBLE_ITINERARY_MESSAGE in plan.errors


def test_no_budget_skips_enforcement():
    plan = OrchestratorAgent().run(
        UserTripRequest(destination="Paris", number_of_days=2, interests=["Food"])
    )
    assert plan.budget_analysis is not None
    assert plan.budget_analysis.within_budget is None
    assert plan.validation_report is not None
    assert plan.validation_report.passed is True


def test_duplicate_pois_are_rejected_by_dedupe_layers(loaded_pois):
    from models.schemas import POIRecommendation

    rec = POIRecommendation(
        poi_id="POI001",
        name="Eiffel Tower",
        category="landmark",
        recommendation_score=0.9,
        rating=4.7,
        visit_duration_hours=2.0,
        estimated_cost=26.0,
        reason="dup",
    )

    class DuplicatePOIAgent(POIRecommendationAgent):
        def run(self, input_data):
            from models.schemas import POIRecommendationList

            return POIRecommendationList(request=input_data, results=[rec, rec])

    plan = OrchestratorAgent(
        poi_agent=DuplicatePOIAgent(loaded_pois),
        pois=loaded_pois,
    ).run(UserTripRequest(destination="Paris", number_of_days=2, budget=500.0))
    # Duplicates are rejected downstream (itinerary dedupes): each POI is
    # scheduled at most once and the plan stays valid.
    assert plan.itinerary.planned_pois.count("POI001") == 1
    assert plan.validation_report is not None
    assert plan.validation_report.passed is True


def test_unknown_poi_destination_fails_gracefully(loaded_pois):
    from models.schemas import POIRecommendation, POIRecommendationList

    ghost = POIRecommendation(
        poi_id="GHOST-1",
        name="Nowhere",
        category="museum",
        recommendation_score=0.9,
        rating=5.0,
        visit_duration_hours=1.0,
        estimated_cost=0.0,
        reason="ghost",
    )

    class GhostPOIAgent(POIRecommendationAgent):
        def run(self, input_data):
            return POIRecommendationList(request=input_data, results=[ghost])

    plan = OrchestratorAgent(
        poi_agent=GhostPOIAgent(loaded_pois), pois=loaded_pois
    ).run(UserTripRequest(destination="Paris", number_of_days=1, budget=500.0))
    assert plan.validation_report is not None
    codes = {v.code for v in plan.validation_report.violations}
    assert "unknown_poi" in codes
    assert plan.errors


def test_weather_api_failure_does_not_crash_planner():
    plan = OrchestratorAgent(
        weather_agent=WeatherAgent(service=ExplodingWeatherService())
    ).run(
        UserTripRequest(
            destination="Jaipur", number_of_days=2, budget=400.0,
            interests=["History"],
        )
    )
    assert plan.itinerary.days
    assert plan.budget_analysis is not None
    assert plan.agent_execution_status.weather is True
    assert plan.weather_report is not None
    assert plan.weather_report.source == "unavailable"


def test_restaurant_api_failure_falls_back_to_dataset():
    plan = OrchestratorAgent(
        restaurant_agent=RestaurantAgent(service=ExplodingPlacesService())
    ).run(
        UserTripRequest(
            destination="Jaipur", number_of_days=2, budget=400.0,
            interests=["Food"],
        )
    )
    assert plan.itinerary.days
    assert plan.restaurant_list is not None
    assert plan.restaurant_list.source == "dataset"
    assert plan.restaurant_list.results


def test_weather_agent_failure_is_recorded():
    plan = OrchestratorAgent(weather_agent=FailingWeatherAgent()).run(
        UserTripRequest(destination="Rome", number_of_days=2)
    )
    assert plan.agent_execution_status.weather is False
    assert any("Weather failed" in error for error in plan.errors)
    assert plan.itinerary.days


def test_restaurant_agent_failure_is_recorded():
    plan = OrchestratorAgent(restaurant_agent=FailingRestaurantAgent()).run(
        UserTripRequest(destination="Rome", number_of_days=2)
    )
    assert plan.agent_execution_status.restaurant is False
    assert any("Restaurant failed" in error for error in plan.errors)
    assert plan.itinerary.days


def test_live_weather_drives_indoor_first_scheduling():
    from datetime import date

    from models.schemas import WeatherDayForecast, WeatherReport

    class RainyWeatherAgent(WeatherAgent):
        def run(self, input_data):
            return WeatherReport(
                destination=input_data.request.destination,
                days=[
                    WeatherDayForecast(
                        date=str(date.today()), day_number=1,
                        condition="Rain", avoid_outdoor=True,
                    ),
                    WeatherDayForecast(
                        date=str(date.today()), day_number=2,
                        condition="Clear sky", avoid_outdoor=False,
                    ),
                ],
                source="live",
                message="Rain expected on Day 1.",
            )

    class EmptyRestaurants(RestaurantAgent):
        def run(self, input_data):
            return RestaurantList(
                request=input_data.request, results=[], source="dataset"
            )

    plan = OrchestratorAgent(
        weather_agent=RainyWeatherAgent(), restaurant_agent=EmptyRestaurants()
    ).run(
        UserTripRequest(
            destination="Jaipur",
            number_of_days=2,
            budget=400.0,
            interests=["History", "Architecture"],
        )
    )
    assert plan.weather_report is not None
    assert plan.weather_report.source == "live"
    assert plan.agent_execution_status.weather is True
    assert plan.validation_report is not None
    assert plan.validation_report.passed is True
    first_day = plan.itinerary.days[0]
    assert first_day.items
    assert first_day.items[0].poi_id in {
        rec.poi_id for rec in plan.recommended_pois if rec.setting == "indoor"
    }