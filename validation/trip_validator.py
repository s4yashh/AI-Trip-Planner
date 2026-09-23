"""Dedicated validation layer checked before any plan is returned.

The validator never mutates the plan: it reports violations and the
orchestrator performs controlled re-planning (up to ``MAX_REPLAN_ATTEMPTS``).
Every check maps to an academic accuracy requirement: destination
correctness, exact day count, duplicates, POI existence, time overlaps,
durations, opening hours, travel realism, budget constraint, budget sums,
restaurant budget fit and weather respect.
"""

from __future__ import annotations

import os

from agents.restaurant_agent import affordable_price_level
from models.schemas import (
    BudgetAnalysis,
    ItineraryResponse,
    POI,
    POIRecommendation,
    RestaurantList,
    UserTripRequest,
    ValidationReport,
    ValidationViolation,
    WeatherReport,
)

MAX_REPLAN_ATTEMPTS = int(os.environ.get("MAX_REPLAN_ATTEMPTS", "3"))


def _minutes(text: str) -> int:
    hours, minutes = text.split(":")
    return int(hours) * 60 + int(minutes)


class TripValidator:
    """Stateless checker for candidate trip plans."""

    def validate(
        self,
        request: UserTripRequest,
        ranked: list[POIRecommendation],
        itinerary: ItineraryResponse,
        budget: BudgetAnalysis | None,
        weather: WeatherReport | None = None,
        restaurants: RestaurantList | None = None,
        daily_food_budget: float | None = None,
        pois: list[POI] | None = None,
        attempts: int = 0,
    ) -> ValidationReport:
        violations: list[ValidationViolation] = []
        by_id = {rec.poi_id: rec for rec in ranked}
        destinations = {poi.poi_id: poi.destination for poi in (pois or [])}
        target = request.destination.strip().lower()

        for rec in ranked:
            destination = destinations.get(rec.poi_id)
            if destination is None:
                violations.append(
                    ValidationViolation(
                        code="unknown_poi",
                        message=f"Recommended POI {rec.poi_id} does not exist "
                        "in the dataset.",
                    )
                )
            elif destination.strip().lower() != target:
                violations.append(
                    ValidationViolation(
                        code="destination_mismatch",
                        message=f"Recommended POI {rec.poi_id} belongs to "
                        f"'{destination}', not '{request.destination}'.",
                    )
                )

        if len(itinerary.days) != request.number_of_days:
            violations.append(
                ValidationViolation(
                    code="day_count",
                    message=f"Itinerary has {len(itinerary.days)} day(s), "
                    f"requested {request.number_of_days}.",
                )
            )

        planned = itinerary.planned_pois
        if len(set(planned)) != len(planned):
            violations.append(
                ValidationViolation(
                    code="duplicate_poi",
                    message="Duplicate POIs scheduled in the itinerary.",
                )
            )
        for poi_id in planned:
            if poi_id not in by_id:
                violations.append(
                    ValidationViolation(
                        code="unknown_poi",
                        message=f"Scheduled POI {poi_id} was never recommended.",
                    )
                )

        for day in itinerary.days:
            previous_end: int | None = None
            for item in day.items:
                start, end = _minutes(item.start_time), _minutes(item.end_time)
                if end - start <= 0:
                    violations.append(
                        ValidationViolation(
                            code="duration_invalid",
                            message=f"{item.name} on day {day.day_number} has "
                            "a non-positive visit duration.",
                        )
                    )
                elif abs((end - start) - item.duration_hours * 60) > 1.0:
                    violations.append(
                        ValidationViolation(
                            code="duration_mismatch",
                            message=f"{item.name} on day {day.day_number}: "
                            "end_time - start_time does not match duration_hours.",
                        )
                    )
                if previous_end is not None and start < previous_end:
                    violations.append(
                        ValidationViolation(
                            code="time_overlap",
                            message=f"{item.name} on day {day.day_number} "
                            "overlaps the previous visit.",
                        )
                    )
                rec = by_id.get(item.poi_id)
                if rec is not None:
                    if rec.open_hour is not None and start < rec.open_hour * 60:
                        violations.append(
                            ValidationViolation(
                                code="opening_hours",
                                message=f"{item.name} starts before its opening hour.",
                            )
                        )
                    if rec.close_hour is not None and end > rec.close_hour * 60:
                        violations.append(
                            ValidationViolation(
                                code="opening_hours",
                                message=f"{item.name} ends after its closing hour.",
                            )
                        )
                previous_end = end if previous_end is None else max(previous_end, end)
            for first, second in zip(day.items, day.items[1:]):
                if first.travel_minutes_to_next is not None:
                    gap = _minutes(second.start_time) - _minutes(first.end_time)
                    if gap + 1.0 < first.travel_minutes_to_next:
                        violations.append(
                            ValidationViolation(
                                code="travel_gap",
                                message=f"Travel to {second.name} on day "
                                f"{day.day_number} is shorter than the routed time.",
                            )
                        )

        if budget is not None:
            components = (
                budget.accommodation
                + budget.transportation
                + budget.food
                + budget.activities
                + budget.miscellaneous
            )
            if abs(components - budget.total_cost) > 0.01:
                violations.append(
                    ValidationViolation(
                        code="budget_sum",
                        message="Budget components do not sum to the total cost.",
                    )
                )
            if request.budget is not None and budget.total_cost > request.budget + 1e-6:
                violations.append(
                    ValidationViolation(
                        code="over_budget",
                        message=f"Total ${budget.total_cost:.2f} exceeds "
                        f"budget ${request.budget:.2f}.",
                    )
                )

        if restaurants is not None and daily_food_budget is not None:
            affordable = affordable_price_level(daily_food_budget)
            for item in restaurants.results:
                if item.price_level > affordable + 1:
                    violations.append(
                        ValidationViolation(
                            code="restaurant_over_budget",
                            message=f"{item.name} (price level {item.price_level}) "
                            "is far above the daily food budget.",
                        )
                    )

        if weather is not None and weather.source == "live":
            bad_days = {
                day.day_number for day in weather.days if day.avoid_outdoor
            }
            for day in itinerary.days:
                if day.day_number not in bad_days:
                    continue
                for item in day.items:
                    rec = by_id.get(item.poi_id)
                    if rec is not None and (rec.setting or "outdoor") == "outdoor":
                        violations.append(
                            ValidationViolation(
                                code="weather_violation",
                                message=f"Outdoor visit {item.name} scheduled on "
                                f"day {day.day_number} despite bad weather.",
                            )
                        )

        return ValidationReport(
            passed=not violations,
            violations=violations,
            attempts=attempts,
            max_attempts=MAX_REPLAN_ATTEMPTS,
        )
