"""Orchestrator agent coordinating the specialised trip-planning agents."""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.poi_agent import POIRecommendationAgent
from agents.restaurant_agent import RestaurantAgent
from agents.weather_agent import WeatherAgent, setting_for_category
from models.schemas import (
    AgentExecutionStatus,
    BudgetRequest,
    ItineraryRequest,
    ItineraryResponse,
    POI,
    POIRecommendationList,
    RestaurantList,
    RestaurantRequest,
    TripPlan,
    UserTripRequest,
    ValidationReport,
    WeatherReport,
    WeatherRequest,
)
from services.routing_service import RoutingService
from utils.data_loader import DEFAULT_POI_DATASET, load_poi_csv
from validation.trip_validator import MAX_REPLAN_ATTEMPTS, TripValidator

logger = logging.getLogger(__name__)

NO_FEASIBLE_ITINERARY_MESSAGE = "No feasible itinerary found within the specified budget."


class OrchestratorAgent(BaseAgent):
    """Coordinates the POI, weather, restaurant, itinerary, budget and
    validation stages end-to-end.

    The orchestrator only wires agents together; it does not implement
    recommendation, scheduling or budget logic itself. Each specialised
    agent stays independently usable. Optional stages (weather,
    restaurant, routing) degrade gracefully and never crash the plan.
    """

    name = "orchestrator-agent"

    def __init__(
        self,
        poi_agent: POIRecommendationAgent | None = None,
        weather_agent: WeatherAgent | None = None,
        restaurant_agent: RestaurantAgent | None = None,
        itinerary_agent: ItineraryAgent | None = None,
        budget_agent: BudgetAgent | None = None,
        validator: TripValidator | None = None,
        routing_service: RoutingService | None = None,
        top_k: int | None = 12,
        pois: list[POI] | None = None,
        max_replan_attempts: int = MAX_REPLAN_ATTEMPTS,
    ) -> None:
        if pois is None:
            pois = load_poi_csv(DEFAULT_POI_DATASET)
        self._pois = pois
        self._poi_agent = poi_agent or POIRecommendationAgent(pois)
        self._weather_agent = weather_agent or WeatherAgent()
        self._restaurant_agent = restaurant_agent or RestaurantAgent()
        self._itinerary_agent = itinerary_agent or ItineraryAgent()
        self._budget_agent = budget_agent or BudgetAgent()
        self._validator = validator or TripValidator()
        self._routing_service = routing_service or RoutingService()
        self._top_k = top_k
        if max_replan_attempts < 1:
            raise ValueError("max_replan_attempts must be at least 1")
        self._max_replan_attempts = max_replan_attempts
        for agent in (
            self._poi_agent,
            self._weather_agent,
            self._restaurant_agent,
            self._itinerary_agent,
            self._budget_agent,
        ):
            if not isinstance(agent, BaseAgent):
                raise ValueError(f"injected agent must subclass BaseAgent, got {type(agent)}")

    def run(self, input_data: Any) -> TripPlan:
        if not isinstance(input_data, UserTripRequest):
            raise ValueError("input_data must be a UserTripRequest")
        request = input_data

        status = AgentExecutionStatus()
        errors: list[str] = []

        recommendations = self._run_recommendation(request, status, errors)
        ranked = recommendations.results if recommendations else []
        ranked = [
            rec.model_copy(update={"setting": setting_for_category(rec.category)})
            for rec in ranked
        ]

        centroid = self._centroid(ranked)
        weather = self._run_weather(request, centroid, status, errors)
        restaurants = self._run_restaurants(request, centroid, status, errors)
        travel, travel_source = self._travel_legs(ranked)

        if not ranked:
            return TripPlan(
                request=request,
                trip_summary=self._trip_summary(request, [], None, None),
                recommended_pois=[],
                weather_report=weather,
                restaurant_list=restaurants,
                itinerary=ItineraryResponse(),
                budget_analysis=None,
                validation_report=None,
                agent_execution_status=status,
                errors=errors,
            )

        batch = ranked if self._top_k is None else ranked[: self._top_k]
        bad_days = [
            day.day_number
            for day in (weather.days if weather else [])
            if day.avoid_outdoor
        ]
        return self._plan_with_validation(
            request, ranked, batch, weather, restaurants, travel,
            travel_source, bad_days, status, errors,
        )

    # ------------------------------------------------------------------ #
    # stages
    # ------------------------------------------------------------------ #

    def _run_recommendation(
        self,
        request: UserTripRequest,
        status: AgentExecutionStatus,
        errors: list[str],
    ) -> POIRecommendationList | None:
        try:
            result = self._poi_agent.run(request)
            status.poi_recommendation = True
            if not result.results:
                errors.append(
                    f"No POIs recommended for destination '{request.destination}'."
                )
            return result
        except Exception as exc:  # noqa: BLE001 - captured as agent failure
            logger.exception("POI recommendation agent failed")
            errors.append(f"POI recommendation failed: {exc}")
            return None

    def _run_weather(
        self,
        request: UserTripRequest,
        centroid: tuple[float, float] | None,
        status: AgentExecutionStatus,
        errors: list[str],
    ) -> WeatherReport | None:
        try:
            latitude, longitude = centroid if centroid else (None, None)
            report = self._weather_agent.run(
                WeatherRequest(
                    request=request, latitude=latitude, longitude=longitude
                )
            )
            status.weather = True
            return report
        except Exception as exc:  # noqa: BLE001 - captured as agent failure
            logger.exception("Weather agent failed")
            errors.append(f"Weather failed: {exc}")
            return None

    def _run_restaurants(
        self,
        request: UserTripRequest,
        centroid: tuple[float, float] | None,
        status: AgentExecutionStatus,
        errors: list[str],
    ) -> RestaurantList | None:
        try:
            latitude, longitude = centroid if centroid else (None, None)
            result = self._restaurant_agent.run(
                RestaurantRequest(
                    request=request,
                    latitude=latitude,
                    longitude=longitude,
                    daily_food_budget=self._budget_agent.daily_food_rate,
                )
            )
            status.restaurant = True
            return result
        except Exception as exc:  # noqa: BLE001 - captured as agent failure
            logger.exception("Restaurant agent failed")
            errors.append(f"Restaurant failed: {exc}")
            return None

    def _run_itinerary(
        self,
        request: UserTripRequest,
        batch: list,
        travel: dict[str, float],
        travel_source: str | None,
        bad_days: list[int],
        status: AgentExecutionStatus,
        errors: list[str],
    ):
        try:
            result = self._itinerary_agent.run(
                ItineraryRequest(
                    number_of_days=request.number_of_days,
                    ranked_pois=batch,
                    travel_minutes=travel,
                    travel_source=travel_source,
                    bad_weather_days=bad_days,
                )
            )
            status.itinerary = True
            return result
        except Exception as exc:  # noqa: BLE001 - captured as agent failure
            logger.exception("Itinerary agent failed")
            errors.append(f"Itinerary failed: {exc}")
            return ItineraryResponse()

    def _run_budget(
        self,
        request: UserTripRequest,
        itinerary,
        ranked: list,
        status: AgentExecutionStatus,
        errors: list[str],
    ):
        if not itinerary.days:
            errors.append("Budget skipped: no itinerary generated.")
            return None
        try:
            result = self._budget_agent.run(
                BudgetRequest(request=request, itinerary=itinerary, pois=ranked)
            )
            status.budget = True
            return result
        except Exception as exc:  # noqa: BLE001 - captured as agent failure
            logger.exception("Budget agent failed")
            errors.append(f"Budget failed: {exc}")
            return None

    # ------------------------------------------------------------------ #
    # validation / re-planning loop
    # ------------------------------------------------------------------ #

    def _plan_with_validation(
        self,
        request,
        ranked,
        batch,
        weather,
        restaurants,
        travel,
        travel_source,
        bad_days,
        status,
        errors,
    ) -> TripPlan:
        report: ValidationReport | None = None
        itinerary = ItineraryResponse()
        budget = None
        attempts = 0
        current_restaurants = restaurants
        notes: list[str] = []

        while attempts < self._max_replan_attempts:
            attempts += 1
            itinerary = self._run_itinerary(
                request, batch, travel, travel_source, bad_days, status, errors
            )
            itinerary, budget = self._converge_budget(
                request, ranked, batch, itinerary, travel, travel_source,
                bad_days, status, errors, notes,
            )
            if budget is None:
                itinerary = ItineraryResponse()
                break
            if request.budget is not None and not itinerary.planned_pois:
                # Nothing schedulable within budget: record one final
                # validation documenting the failure, then stop.
                report = self._validator.validate(
                    request,
                    ranked,
                    itinerary,
                    budget,
                    weather=weather,
                    restaurants=current_restaurants,
                    daily_food_budget=self._budget_agent.daily_food_rate,
                    pois=self._pois,
                    attempts=attempts,
                )
                status.validator = True
                break
            report = self._validator.validate(
                request,
                ranked,
                itinerary,
                budget,
                weather=weather,
                restaurants=current_restaurants,
                daily_food_budget=self._budget_agent.daily_food_rate,
                pois=self._pois,
                attempts=attempts,
            )
            status.validator = True
            if report.passed:
                break
            current_restaurants, fixed = self._fix_non_budget(
                batch, itinerary, report, current_restaurants, notes
            )
            if not fixed:
                break

        if report is not None:
            report = report.model_copy(update={"notes": notes})

        if budget is not None and report is not None and report.passed:
            assert request.budget is None or budget.total_cost <= request.budget + 1e-6
            return TripPlan(
                request=request,
                trip_summary=self._trip_summary(
                    request, ranked, itinerary, budget,
                    current_restaurants, weather,
                ),
                recommended_pois=ranked,
                weather_report=weather,
                restaurant_list=current_restaurants,
                itinerary=itinerary,
                budget_analysis=budget,
                validation_report=report,
                agent_execution_status=status,
                errors=errors,
            )
        return self._infeasible(
            request, weather, current_restaurants, report, status, errors, budget
        )

    def _converge_budget(
        self,
        request,
        ranked,
        batch,
        itinerary,
        travel,
        travel_source,
        bad_days,
        status,
        errors,
        notes,
    ):
        """Recompute the budget, pruning the priciest scheduled POI and
        re-scheduling until the total fits the user's budget (or nothing
        scheduled remains). The budget agent stays the sole validator of
        the numbers; this loop only drives re-planning.

        Returns the (itinerary, budget) pair so the final plan always
        matches the validated numbers.
        """
        budget = self._run_budget(request, itinerary, ranked, status, errors)
        if budget is None or request.budget is None:
            return itinerary, budget
        while budget.total_cost > request.budget + 1e-6:
            planned = set(itinerary.planned_pois)
            scheduled = [rec for rec in batch if rec.poi_id in planned]
            if not scheduled:
                break
            priciest = max(scheduled, key=lambda rec: rec.estimated_cost)
            batch[:] = [rec for rec in batch if rec.poi_id != priciest.poi_id]
            notes.append(
                f"Budget enforcement: removed {priciest.name} "
                f"(${priciest.estimated_cost:.2f}) to meet the budget."
            )
            itinerary = self._run_itinerary(
                request, batch, travel, travel_source, bad_days, status, errors
            )
            budget = self._run_budget(request, itinerary, ranked, status, errors)
            if budget is None:
                return itinerary, None
        return itinerary, budget

    def _fix_non_budget(self, batch, itinerary, report, restaurants, notes):
        """Fix validation failures other than the budget.

        Returns (restaurants, fixed). Budget violations are handled by
        :meth:`_converge_budget`; anything unfixable returns False so the
        loop stops instead of spinning.
        """
        codes = {violation.code for violation in report.violations}
        current = restaurants
        if "restaurant_over_budget" in codes:
            current = self._drop_over_budget_restaurants(restaurants, report, notes)
        if "over_budget" in codes:
            # Budget convergence already removed everything it could.
            return current, False
        remaining = codes - {"restaurant_over_budget"}
        if not remaining:
            return current, True
        if remaining == {"weather_violation"}:
            planned = set(itinerary.planned_pois)
            offender = next(
                (
                    violation for violation in report.violations
                    if violation.code == "weather_violation"
                ),
                None,
            )
            if offender is None:
                return current, False
            for rec in list(batch):
                if rec.poi_id in planned and rec.name in offender.message:
                    batch.remove(rec)
                    notes.append(
                        f"Re-planning: removed {rec.name} from a rainy day "
                        f"(attempt {report.attempts})."
                    )
                    return current, True
            return current, False
        return current, False

    @staticmethod
    def _drop_over_budget_restaurants(restaurants, report, notes: list[str]):
        """Filter restaurants the validator flagged, keeping the itinerary."""
        if restaurants is None:
            return None
        flagged = {
            violation.message.split(" (price level")[0]
            for violation in report.violations
            if violation.code == "restaurant_over_budget"
        }
        kept = [item for item in restaurants.results if item.name not in flagged]
        removed = len(restaurants.results) - len(kept)
        if removed:
            notes.append(
                f"Re-planning: removed {removed} restaurant(s) above the "
                f"daily food budget (attempt {report.attempts})."
            )
        return restaurants.model_copy(update={"results": kept})

    def _infeasible(
        self, request, weather, restaurants, report, status, errors, budget
    ) -> TripPlan:
        codes = (
            {violation.code for violation in report.violations}
            if report is not None
            else set()
        )
        if "over_budget" in codes or (
            budget is not None
            and request.budget is not None
            and not codes - {"restaurant_over_budget"}
        ):
            message = NO_FEASIBLE_ITINERARY_MESSAGE
        elif report is not None and not report.passed:
            details = "; ".join(
                violation.message for violation in report.violations[:3]
            )
            message = f"Trip plan failed validation: {details}"
        else:
            message = "Trip planning failed before a budget could be estimated."
        errors.append(message)
        return TripPlan(
            request=request,
            trip_summary=message,
            recommended_pois=[],
            weather_report=weather,
            restaurant_list=restaurants,
            itinerary=ItineraryResponse(),
            budget_analysis=None,
            validation_report=report,
            agent_execution_status=status,
            errors=errors,
        )

    # ------------------------------------------------------------------ #
    # helpers
    # ------------------------------------------------------------------ #

    def _centroid(self, ranked: list) -> tuple[float, float] | None:
        by_id = {poi.poi_id: poi for poi in self._pois}
        latitudes = [
            by_id[rec.poi_id].latitude for rec in ranked if rec.poi_id in by_id
        ]
        longitudes = [
            by_id[rec.poi_id].longitude for rec in ranked if rec.poi_id in by_id
        ]
        if not latitudes:
            return None
        return sum(latitudes) / len(latitudes), sum(longitudes) / len(longitudes)

    def _travel_legs(self, ranked: list) -> tuple[dict[str, float], str | None]:
        points = [
            (rec.poi_id, rec.latitude, rec.longitude)
            for rec in ranked
            if rec.latitude is not None and rec.longitude is not None
        ]
        if len(points) < 2:
            return {}, None
        try:
            return self._routing_service.pairwise_minutes(points)
        except Exception as exc:  # noqa: BLE001 - routing never blocks planning
            logger.warning("Routing service failed: %s", exc)
            return {}, None

    @staticmethod
    def _trip_summary(
        request, ranked, itinerary, budget, restaurants=None, weather=None
    ) -> str:
        days = request.number_of_days
        destination = request.destination
        if itinerary is None:
            return (
                f"Personalised {days}-day trip to {destination}. "
                "No POIs recommended."
            )
        planned = len(itinerary.planned_pois)
        parts = [
            f"Personalised {days}-day trip to {destination}",
            f"{len(ranked)} POIs recommended",
            f"{itinerary.days_used} day(s) of itinerary generated ({planned} POIs scheduled)",
        ]
        if restaurants is not None and restaurants.results:
            parts.append(f"{len(restaurants.results)} restaurant(s) ranked")
        if weather is not None and weather.source == "live":
            rainy = [day.day_number for day in weather.days if day.avoid_outdoor]
            if rainy:
                parts.append(
                    "bad weather expected on day(s) "
                    + ", ".join(str(number) for number in rainy)
                )
        if budget is not None:
            parts.append(f"estimated total ${budget.total_cost:.2f}")
            if budget.within_budget is True:
                parts.append(f"within budget (${budget.remaining_budget:.2f} to spare)")
            elif budget.within_budget is False:
                parts.append(f"${-budget.remaining_budget:.2f} over budget")
        return ". ".join(parts) + "."
