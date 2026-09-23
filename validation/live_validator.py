"""Live-trip checks extending the existing independent validation layer."""
from datetime import timedelta

from utils.opening_hours import indoor, minutes, windows
from validation.trip_validator import TripValidator


class LiveTripValidator(TripValidator):
    def validate_live(self, prefs, plan, previous=()):
        conflicts = []
        if not plan.activities:
            conflicts.append("No feasible activities found for these dates and preferences.")
        ids = [a.place.id for a in plan.activities]
        if len(ids) != len(set(ids)):
            conflicts.append("Duplicate activities in itinerary.")
        known = {p.id for p in plan.places} | {a.place.id for a in previous}
        last_day = prefs.start_date + timedelta(days=prefs.number_of_days-1)
        bad = {w.date for w in plan.weather if w.avoid_outdoor}
        for activity in plan.activities:
            if activity.place.id not in known:
                conflicts.append(f"Unknown place: {activity.place.name}.")
            if not prefs.start_date <= activity.date <= last_day:
                conflicts.append(f"{activity.place.name} is outside the trip dates; adjust the protected activity first.")
            start, end = minutes(activity.start_time), minutes(activity.end_time)
            if end-start != activity.duration_minutes:
                conflicts.append(f"Invalid duration for {activity.place.name}.")
            hours = windows(activity.place.opening_hours, activity.date)
            if not activity.completed and hours is not None and not any(start >= a and end <= b for a, b in hours):
                conflicts.append(f"{activity.place.name} is closed during its planned visit.")
            if not activity.completed and activity.date in bad and not indoor(activity.place):
                conflicts.append(f"Weather affects outdoor activity {activity.place.name}.")
        ordered = sorted(plan.activities, key=lambda a: (a.date, a.start_time))
        routes = {(r.from_id, r.to_id): r for r in plan.routes}
        for first, second in zip(ordered, ordered[1:]):
            if first.date != second.date:
                continue
            gap = minutes(second.start_time)-minutes(first.end_time)
            route = routes.get((first.place.id, second.place.id))
            if gap < 0 or (route and route.minutes is not None and gap < route.minutes):
                conflicts.append(f"Insufficient travel time between {first.place.name} and {second.place.name}.")
        for old in previous:
            current = next((a for a in plan.activities if a.id == old.id), None)
            if old.locked or old.completed or old.committed:
                if current is None or (old.date, old.start_time, old.end_time) != (current.date, current.start_time, current.end_time):
                    conflicts.append(f"Protected activity {old.place.name} was moved.")
        if plan.budget.within_budget is False:
            conflicts.append("Known projected costs exceed the trip budget. Update allowances, expenses, or budget.")
        return list(dict.fromkeys(conflicts))
