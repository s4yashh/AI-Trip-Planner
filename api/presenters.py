"""Serialise a TripPlan into the JSON contract consumed by the frontend."""

from __future__ import annotations

import os
import re

INR_PER_USD = float(os.environ.get("INR_PER_USD", "83.0"))
CURRENCY_RATES = {"INR": INR_PER_USD, "USD": 1.0}
CURRENCY_SYMBOLS = {"INR": "\u20b9", "USD": "$"}

_USD_PATTERN = re.compile(r"\$(\d+(?:\.\d+)?)")


def rate_for(currency: str) -> float:
    return CURRENCY_RATES.get((currency or "USD").upper(), 1.0)


def convert(usd_amount: float, currency: str) -> float:
    return round(usd_amount * rate_for(currency), 2) if usd_amount is not None else None


def format_money(amount: float, currency: str) -> str:
    """Format a numeric amount with thousands separators and currency symbol."""
    symbol = CURRENCY_SYMBOLS.get((currency or "USD").upper(), "")
    if amount is None:
        return ""
    return f"{symbol}{amount:,.0f}".replace("$-", "-$")


def translate_basis(basis: str, currency: str) -> str:
    """Rewrite a budget breakdown basis into the requested currency."""
    if (currency or "USD").upper() == "USD":
        return basis
    rate = rate_for(currency)
    symbol = CURRENCY_SYMBOLS[(currency or "USD").upper()]

    def _replace(match: re.Match) -> str:
        value = float(match.group(1)) * rate
        return f"{symbol}{value:,.0f}"

    return _USD_PATTERN.sub(_replace, basis)


def build_trip_response(plan, currency: str) -> dict:
    budget_analysis = plan.budget_analysis

    trip_summary = {
        "destination": plan.request.destination,
        "number_of_days": plan.request.number_of_days,
        "budget": convert(plan.request.budget, currency),
        "interests": plan.request.interests,
        "currency": (currency or "USD").upper(),
        "message": message_for(plan, currency),
        "recommended_count": len(plan.recommended_pois),
        "days_generated": plan.itinerary.days_used,
        "total_estimated_cost": (
            convert(budget_analysis.total_cost, currency) if budget_analysis else None
        ),
    }

    recommended_pois = [
        {
            "poi_id": rec.poi_id,
            "name": rec.name,
            "category": rec.category,
            "recommendation_score": round(rec.recommendation_score, 4),
            "rating": rec.rating,
            "visit_duration_hours": rec.visit_duration_hours,
            "estimated_cost": convert(rec.estimated_cost, currency),
            "reason": rec.reason,
        }
        for rec in plan.recommended_pois
    ]

    itinerary = {
        "days": [
            {
                "day_number": day.day_number,
                "items": [
                    {
                        "poi_id": item.poi_id,
                        "name": item.name,
                        "start_time": item.start_time,
                        "end_time": item.end_time,
                        "duration_hours": item.duration_hours,
                        "estimated_cost": convert(item.estimated_cost, currency),
                    }
                    for item in day.items
                ],
            }
            for day in plan.itinerary.days
        ],
        "skipped_poi_ids": plan.itinerary.skipped_poi_ids,
    }

    budget_payload = None
    if budget_analysis is not None:
        budget_payload = {
            "accommodation": convert(budget_analysis.accommodation, currency),
            "transportation": convert(budget_analysis.transportation, currency),
            "food": convert(budget_analysis.food, currency),
            "activities": convert(budget_analysis.activities, currency),
            "miscellaneous": convert(budget_analysis.miscellaneous, currency),
            "total_cost": convert(budget_analysis.total_cost, currency),
            "user_budget": convert(budget_analysis.user_budget, currency),
            "within_budget": budget_analysis.within_budget,
            "remaining_budget": convert(budget_analysis.remaining_budget, currency),
            "suggestions": budget_analysis.suggestions,
            "breakdown": [
                {
                    "category": item.category,
                    "amount": convert(item.amount, currency),
                    "basis": translate_basis(item.basis, currency),
                }
                for item in budget_analysis.breakdown
            ],
        }

    status = plan.agent_execution_status
    agent_execution_status = {
        "orchestrator": True,
        "poi_recommendation": status.poi_recommendation,
        "itinerary": status.itinerary,
        "budget": status.budget,
        "lines": status.to_text(),
    }

    return {
        "trip_summary": trip_summary,
        "recommended_pois": recommended_pois,
        "itinerary": itinerary,
        "budget_analysis": budget_payload,
        "agent_execution_status": agent_execution_status,
        "errors": plan.errors,
    }


def message_for(plan, currency: str) -> str:
    request = plan.request
    parts = [
        f"Personalised {request.number_of_days}-day trip to {request.destination}",
        f"{len(plan.recommended_pois)} POIs recommended",
        f"{plan.itinerary.days_used} day(s) of itinerary generated",
    ]
    budget = plan.budget_analysis
    if budget is not None:
        total = format_money(convert(budget.total_cost, currency), currency)
        parts.append(f"estimated total {total}")
        if budget.within_budget is True:
            remaining = format_money(convert(budget.remaining_budget, currency), currency)
            parts.append(f"within budget ({remaining} to spare)")
        elif budget.within_budget is False:
            exceeded = format_money(convert(-budget.remaining_budget, currency), currency)
            parts.append(f"{exceeded} over budget")
    return ". ".join(parts) + "."