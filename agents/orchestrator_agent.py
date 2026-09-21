"""Orchestrator agent coordinating the specialised trip-planning agents."""

from __future__ import annotations

import logging
from typing import Any

from agents.base_agent import BaseAgent
from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.poi_agent import POIRecommendationAgent
from models.schemas import (
    AgentExecutionStatus,
    BudgetRequest,
    ItineraryRequest,
    ItineraryResponse,
    POI,
    POIRecommendationList,
    TripPlan,
    UserTripRequest,
)
from utils.data_loader import DEFAULT_POI_DATASET, load_poi_csv

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Coordinates the POI, itinerary and budget agents end-to-end.

    The orchestrator only wires agents together; it does not implement
    recommendation, scheduling or budget logic itself. Each specialised
    agent stays independently usable.
    """

    name = "orchestrator-agent"

    def __init__(
        self,
        poi_agent: POIRecommendationAgent | None = None,
        itinerary_agent: ItineraryAgent | None = None,
        budget_agent: BudgetAgent | None = None,
        top_k: int | None = 12,
        pois: list[POI] | None = None,
    ) -> None:
        if pois is None:
            pois = load_poi_csv(DEFAULT_POI_DATASET)
        self._poi_agent = poi_agent or POIRecommendationAgent(pois)
        self._itinerary_agent = itinerary_agent or ItineraryAgent()
        self._budget_agent = budget_agent or BudgetAgent()
        self._top_k = top_k
        for agent in (self._poi_agent, self._itinerary_agent, self._budget_agent):
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

        itinerary = self._run_itinerary(request, ranked, status, errors)
        budget = self._run_budget(request, itinerary, ranked, status, errors)

        return TripPlan(
            request=request,
            trip_summary=self._trip_summary(request, ranked, itinerary, budget),
            recommended_pois=ranked,
            itinerary=itinerary,
            budget_analysis=budget,
            agent_execution_status=status,
            errors=errors,
        )

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

    def _run_itinerary(
        self,
        request: UserTripRequest,
        ranked: list,
        status: AgentExecutionStatus,
        errors: list[str],
    ):
        if not ranked:
            errors.append("Itinerary skipped: no POIs to schedule.")
            return ItineraryResponse()
        try:
            batch = ranked if self._top_k is None else ranked[: self._top_k]
            result = self._itinerary_agent.run(
                ItineraryRequest(number_of_days=request.number_of_days, ranked_pois=batch)
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

    @staticmethod
    def _trip_summary(request, ranked, itinerary, budget) -> str:
        days = request.number_of_days
        destination = request.destination
        planned = len(itinerary.planned_pois)
        parts = [
            f"Personalised {days}-day trip to {destination}",
            f"{len(ranked)} POIs recommended",
            f"{itinerary.days_used} day(s) of itinerary generated ({planned} POIs scheduled)",
        ]
        if budget is not None:
            parts.append(f"estimated total ${budget.total_cost:.2f}")
            if budget.within_budget is True:
                parts.append(f"within budget (${budget.remaining_budget:.2f} to spare)")
            elif budget.within_budget is False:
                parts.append(f"${-budget.remaining_budget:.2f} over budget")
        return ". ".join(parts) + "."