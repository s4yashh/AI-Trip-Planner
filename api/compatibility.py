"""Legacy /trip response shape, retaining nulls for unavailable monetary facts."""
from datetime import timedelta


def legacy_response(trip):
    prefs, plan = trip.preferences, trip.plan
    days = []
    for offset in range(prefs.number_of_days):
        day = prefs.start_date + timedelta(days=offset)
        days.append({"day_number": offset+1, "items": [{
            "poi_id": a.place.id, "name": a.place.name, "start_time": a.start_time, "end_time": a.end_time,
            "duration_hours": a.duration_minutes/60, "estimated_cost": None,
            "travel_minutes_to_next": next((r.minutes for r in plan.routes if r.from_id == a.place.id), None),
            "travel_source": next((r.source.status for r in plan.routes if r.from_id == a.place.id), None),
        } for a in plan.activities if a.date == day]})
    message = f"{prefs.number_of_days}-day trip to {prefs.destination}. " + ("Itinerary validated." if plan.valid else "Review planning conflicts.")
    budget = {line.category: line.projected for line in plan.budget.lines}
    budget.update({"total_cost": plan.budget.total, "user_budget": prefs.budget,
                   "within_budget": plan.budget.within_budget, "remaining_budget": plan.budget.remaining,
                   "complete": plan.budget.complete, "suggestions": plan.warnings,
                   "breakdown": [{"category": l.category, "amount": l.projected, "basis": l.basis} for l in plan.budget.lines]})
    return {"trip_id": trip.id, "version": trip.version,
        "trip_summary": {"destination": prefs.destination, "number_of_days": prefs.number_of_days,
            "budget": prefs.budget, "currency": prefs.currency, "interests": prefs.interests,
            "message": message, "recommended_count": len(plan.places), "total_estimated_cost": plan.budget.total},
        "recommended_pois": [{"poi_id": p.id, "name": p.name, "category": p.kind,
            "recommendation_score": p.score, "rating": None, "estimated_cost": None,
            "visit_duration_hours": {"relaxed": 2, "balanced": 1.5, "busy": 1}[prefs.pace],
            "reason": p.reason, "latitude": p.latitude, "longitude": p.longitude} for p in plan.places],
        "itinerary": {"days": days, "skipped_poi_ids": [], "travel_source": "mixed"},
        "weather_report": {"source": plan.sources.get("weather").status if plan.sources.get("weather") else "unavailable",
                           "days": [w.model_dump(mode="json") for w in plan.weather]},
        "restaurant_list": {"source": plan.sources.get("places").status if plan.sources.get("places") else "unavailable",
                            "results": [p.model_dump(mode="json") for p in plan.restaurants]},
        "budget_analysis": budget, "validation_report": {"passed": plan.valid, "attempts": plan.attempts,
            "max_attempts": 3, "notes": plan.warnings, "violations": [{"code": "live_conflict", "message": m} for m in plan.conflicts]},
        "agent_execution_status": {name: status in {"complete", "passed", "live", "cached"} for name, status in plan.agents.items()},
        "errors": plan.conflicts}
