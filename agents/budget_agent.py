"""Transparent, explainable trip budget estimation agent."""

from __future__ import annotations

from typing import Any, Mapping

from agents.base_agent import BaseAgent
from models.schemas import BudgetAnalysis, BudgetItem, BudgetRequest

DEFAULT_RATES = {
    "accommodation_per_night": 25.0,
    "food_per_day": 10.0,
    "transportation_per_day": 8.0,
    "miscellaneous_per_day": 5.0,
}


class BudgetAgent(BaseAgent):
    """Estimates a trip's cost and compares it to the user's budget.

    Activity costs come from the actual POI itinerary; all other
    categories use configurable daily rates because the dataset does
    not contain hotel, transport or dining data.
    """

    name = "budget-agent"

    def __init__(self, rates: Mapping[str, float] | None = None) -> None:
        merged = {**DEFAULT_RATES, **(rates or {})}
        invalid = {
            key: value
            for key, value in merged.items()
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        }
        if invalid:
            raise ValueError(f"rates must be non-negative numbers, got {invalid}")
        self._rates = merged

    @property
    def daily_food_rate(self) -> float:
        """Per-day food estimate, used for restaurant budget compatibility."""
        return float(self._rates["food_per_day"])

    def run(self, input_data: Any) -> BudgetAnalysis:
        if not isinstance(input_data, BudgetRequest):
            raise ValueError("input_data must be a BudgetRequest")

        days = input_data.request.number_of_days
        nights = max(days - 1, 0)
        activities = sum(
            item.estimated_cost
            for day in input_data.itinerary.days
            for item in day.items
        )

        accommodation = nights * self._rates["accommodation_per_night"]
        food = days * self._rates["food_per_day"]
        transportation = days * self._rates["transportation_per_day"]
        miscellaneous = days * self._rates["miscellaneous_per_day"]
        total_cost = accommodation + transportation + food + activities + miscellaneous

        budget = input_data.request.budget
        within_budget: bool | None = None
        remaining: float | None = None
        if budget is not None:
            within_budget = total_cost <= budget
            remaining = budget - total_cost

        breakdown = [
            BudgetItem(
                category="Accommodation",
                amount=accommodation,
                basis=f"{nights} night(s) x ${self._rates['accommodation_per_night']:g}",
            ),
            BudgetItem(
                category="Transportation",
                amount=transportation,
                basis=f"{days} day(s) x ${self._rates['transportation_per_day']:g}",
            ),
            BudgetItem(
                category="Food",
                amount=food,
                basis=f"{days} day(s) x ${self._rates['food_per_day']:g}",
            ),
            BudgetItem(
                category="Activities",
                amount=activities,
                basis=f"{len(input_data.itinerary.planned_pois)} planned POI visit(s)",
            ),
            BudgetItem(
                category="Miscellaneous",
                amount=miscellaneous,
                basis=f"{days} day(s) x ${self._rates['miscellaneous_per_day']:g}",
            ),
        ]

        return BudgetAnalysis(
            accommodation=accommodation,
            transportation=transportation,
            food=food,
            activities=activities,
            miscellaneous=miscellaneous,
            total_cost=total_cost,
            user_budget=budget,
            within_budget=within_budget,
            remaining_budget=remaining,
            suggestions=self._suggestions(budget, total_cost, input_data),
            breakdown=breakdown,
        )

    def _suggestions(
        self, budget: float | None, total_cost: float, request: BudgetRequest
    ) -> list[str]:
        suggestions: list[str] = []
        planned = [
            item for day in request.itinerary.days for item in day.items
        ]

        if budget is None:
            return ["Set a budget to receive within-budget and saving feedback."]

        if total_cost <= budget:
            return []

        days = request.request.number_of_days
        one_day_cut = (
            self._rates["food_per_day"]
            + self._rates["transportation_per_day"]
            + self._rates["miscellaneous_per_day"]
            + self._rates["accommodation_per_night"]
        )
        suggestions.append(
            f"Shorten the trip by one day and one night to save roughly "
            f"${one_day_cut:.2f} (accommodation, food, transport, misc.)"
        )

        if planned:
            priciest = max(planned, key=lambda item: item.estimated_cost)
            if priciest.estimated_cost > 0:
                suggestions.append(
                    f"Replace {priciest.name} (${priciest.estimated_cost:.2f}) "
                    "with a cheaper or free attraction."
                )

        trim_saving = (
            0.10
            * (self._rates["food_per_day"] + self._rates["miscellaneous_per_day"])
            * days
        )
        suggestions.append(
            f"Trim daily food and miscellaneous estimates by about 10% to "
            f"save roughly ${trim_saving:.2f}."
        )
        return suggestions