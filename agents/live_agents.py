"""Specialist live-data agents sharing the existing BaseAgent contract."""
import os
import time
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from agents.base_agent import BaseAgent
from agents.itinerary_agent import ItineraryAgent, _to_hhmm
from models.live import Activity, Budget, BudgetLine, Route, Source, utcnow
from services.live_providers import ProviderError
from services.routing_service import haversine_km
from utils.opening_hours import indoor, minutes, windows
from utils.text_features import TfidfVectorizer, cosine_similarity


class RecommendationAgent(BaseAgent):
    name = "poi_recommendation"

    def run(self, input_data):
        prefs, places = input_data
        candidates = [p.model_copy(deep=True) for p in places if p.kind not in
                      {"restaurant", "cafe", "lodging", "hospital", "pharmacy", "police"}]
        # Reuse the project's dependency-free content similarity algorithm.
        query = " ".join(prefs.interests).lower()
        texts = [" ".join([p.kind, p.name, *p.tags.values()]).lower() for p in candidates]
        vectorizer = TfidfVectorizer().fit(texts + [query])
        query_vector = vectorizer.transform([query])[0]
        for place, vector in zip(candidates, vectorizer.transform(texts)):
            text = " ".join([place.kind, place.name, *place.tags.values()]).lower()
            matches = [interest for interest in prefs.interests if interest.lower() in text]
            place.score = cosine_similarity(query_vector, vector)
            place.reason = "Matches: " + ", ".join(matches) if matches else "Nearby attraction from OpenStreetMap"
        return sorted(candidates, key=lambda p: (-p.score, p.id))[:60]


class LiveRestaurantAgent(BaseAgent):
    name = "restaurant"

    def run(self, input_data):
        prefs, places = input_data
        restaurants = [p.model_copy(deep=True) for p in places if p.kind in {"restaurant", "cafe"}]
        for place in restaurants:
            known = [d for d in prefs.dietary_preferences if place.tags.get("diet:" + d.lower()) in {"yes", "only"}]
            place.score = len(known)
            place.reason = ("Listed dietary options: " + ", ".join(known) if known
                            else "Dietary suitability unknown; confirm with the restaurant")
        return sorted(restaurants, key=lambda p: (-p.score, p.id))[:12]


class AccommodationAgent(BaseAgent):
    name = "accommodation"

    def __init__(self, providers):
        self.providers = providers

    def run(self, input_data):
        prefs, location = input_data
        return self.providers.hotels(prefs, location["latitude"], location["longitude"])


class LiveWeatherAgent(BaseAgent):
    name = "weather"

    def __init__(self, providers):
        self.providers = providers

    def run(self, input_data):
        prefs, location = input_data
        return self.providers.weather(prefs, location["latitude"], location["longitude"])


class TransportationAgent(BaseAgent):
    name = "transportation"

    def __init__(self, providers):
        self.providers = providers
        self.routes = {}
        self.deadline = time.monotonic() + 45

    def run(self, input_data):
        first, second, mode, departure = input_data
        key = (first.id, second.id, mode, (departure or "")[:13])
        if key not in self.routes:
            try:
                if len(self.routes) >= 20 or time.monotonic() >= self.deadline:
                    raise ProviderError("Per-plan route request limit reached; this leg uses a geographic estimate.")
                self.routes[key] = self.providers.route(first, second, mode, departure)
            except ProviderError as exc:
                distance = haversine_km((first.latitude, first.longitude), (second.latitude, second.longitude))
                self.routes[key] = Route(from_id=first.id, to_id=second.id, distance_km=round(distance, 2),
                    minutes=round(distance * 1.4 / (4.5 if mode == "walking" else 25) * 60, 1),
                    source=Source(provider="Geographic estimate", status="estimated", retrieved_at=utcnow(),
                                  message=f"{exc} Straight-line distance × 1.4; traffic unknown."))
        return self.routes[key]


class TrafficAgent(BaseAgent):
    name = "traffic"

    def run(self, input_data):
        routes = input_data
        available = [r for r in routes if r.traffic_delay_minutes is not None]
        return Source(provider="TomTom traffic", status=available[0].source.status if available else "unavailable",
            retrieved_at=available[0].source.retrieved_at if available else None,
            expires_at=available[0].source.expires_at if available else None,
            message="Traffic-aware driving times included." if available else "Live traffic unavailable for these routes.")


class EmergencyAgent(BaseAgent):
    name = "emergency"

    def run(self, input_data):
        return [p for p in input_data if p.kind in {"hospital", "pharmacy", "police"}][:20]


class LiveBudgetAgent(BaseAgent):
    name = "budget"

    def run(self, input_data):
        prefs, hotels, expenses = input_data
        quote = None
        note = None
        amounts = []
        for hotel in hotels:
            amount = hotel.amount
            if hotel.currency != prefs.currency:
                configured = os.getenv("INR_PER_USD", "")
                if not configured or {hotel.currency, prefs.currency} != {"INR", "USD"}:
                    continue
                try:
                    rate = float(configured)
                    if rate <= 0 or not math.isfinite(rate):
                        continue
                except ValueError:
                    continue
                amount = amount * rate if prefs.currency == "INR" else amount / rate
                note = f"User-configured conversion: 1 USD = {rate:g} INR; not a live exchange rate."
            amounts.append(amount)
        if amounts:
            quote = min(amounts)
        lines = []
        for category, allowance in prefs.allowances.model_dump().items():
            planned = quote if category == "accommodation" and quote is not None else allowance
            spent = round(sum(e.amount for e in expenses if e.category == category), 2)
            projected = round(max(planned, spent), 2) if planned is not None else None
            lines.append(BudgetLine(category=category, planned=round(planned, 2) if planned is not None else None,
                spent=spent, projected=projected,
                basis="Lowest available hotel quote for the stay" if category == "accommodation" and quote is not None
                else "Traveler's total-trip allowance" if allowance is not None else "Unknown; enter a total-trip allowance"))
        complete = all(line.projected is not None for line in lines)
        known = round(sum(line.projected if line.projected is not None else line.spent for line in lines), 2)
        total = known if complete else None
        within = None if prefs.budget is None or (not complete and known <= prefs.budget) else known <= prefs.budget
        return Budget(lines=lines, known_total=known, total=total, spent=round(sum(e.amount for e in expenses), 2),
            complete=complete, within_budget=within, remaining=round(prefs.budget-known, 2) if complete and prefs.budget is not None else None,
            conversion_note=note)


class AdaptiveItineraryAgent(ItineraryAgent):
    """Live scheduling extension: preserves commitments and reserves routed gaps."""
    name = "itinerary"

    def __init__(self, transportation):
        super().__init__()
        self.transportation = transportation

    def run(self, input_data):
        prefs, places, weather, old, timezone_name, now = input_data
        local_now = now.astimezone(ZoneInfo(timezone_name))
        durations = {"relaxed": 120, "balanced": 90, "busy": 60}
        daily_count = {"relaxed": 2, "balanced": 3, "busy": 5}[prefs.pace]
        protected = [a.model_copy(deep=True) for a in old if a.locked or a.completed or a.committed or
                     datetime.fromisoformat(f"{a.date}T{a.start_time}").replace(tzinfo=ZoneInfo(timezone_name)) <= local_now]
        scheduled = list(protected)
        used = {a.place.id for a in protected}
        bad_days = {w.date for w in weather if w.avoid_outdoor}
        routes = []
        warnings = []
        # Refresh facts without changing the identity or time of protected activities.
        current = {p.id: p for p in places}
        for activity in scheduled:
            if activity.place.id in current:
                activity.place = current[activity.place.id]
        for offset in range(prefs.number_of_days):
            day = prefs.start_date + timedelta(days=offset)
            if day < local_now.date():
                continue
            day_items = [a for a in scheduled if a.date == day]
            for place in places:
                if len(day_items) >= daily_count:
                    break
                if place.id in used or (day in bad_days and not indoor(place)):
                    continue
                hours = windows(place.opening_hours, day)
                if hours == []:
                    continue
                duration = durations[prefs.pace]
                # Try slots in quarter-hour steps, including gaps around locked reservations.
                earliest = max(540, (local_now.hour * 60 + local_now.minute + 15) if day == local_now.date() else 540)
                earliest = ((earliest + 14) // 15) * 15
                for start in range(earliest, 1080-duration+1, 15):
                    end = start + duration
                    if hours is not None and not any(start >= a and end <= b for a, b in hours):
                        continue
                    if any(start < minutes(a.end_time) and end > minutes(a.start_time) for a in day_items):
                        continue
                    before = max((a for a in day_items if minutes(a.end_time) <= start), key=lambda a: a.end_time, default=None)
                    after = min((a for a in day_items if minutes(a.start_time) >= end), key=lambda a: a.start_time, default=None)
                    possible = True
                    for first, second, gap, depart in [
                        (before.place if before else None, place, start-minutes(before.end_time) if before else 0, before.end_time if before else "09:00"),
                        (place, after.place if after else None, minutes(after.start_time)-end if after else 0, _to_hhmm(end)),
                    ]:
                        if first is None or second is None:
                            continue
                        # Provider cache key is rounded to the departure date to bound calls during slot search.
                        departure = datetime.fromisoformat(f"{day}T{depart}").replace(tzinfo=ZoneInfo(timezone_name))
                        departure = max(departure, local_now)
                        route = self.transportation.run((first, second, prefs.transport_mode, departure.isoformat()))
                        if route.minutes is None or gap < max(15, route.minutes):
                            possible = False
                            break
                    if not possible:
                        continue
                    activity = Activity(id=place.id, place=place, date=day, start_time=_to_hhmm(start),
                                        end_time=_to_hhmm(end), duration_minutes=duration)
                    day_items.append(activity)
                    scheduled.append(activity)
                    used.add(place.id)
                    break
        scheduled.sort(key=lambda a: (a.date, a.start_time))
        for first, second in zip(scheduled, scheduled[1:]):
            if first.date == second.date:
                departure = datetime.fromisoformat(f"{first.date}T{first.end_time}").replace(tzinfo=ZoneInfo(timezone_name))
                if departure < local_now:
                    departure = local_now
                routes.append(self.transportation.run((first.place, second.place, prefs.transport_mode, departure.isoformat())))
        if any(windows(a.place.opening_hours, a.date) is None for a in scheduled):
            warnings.append("Some opening hours are unknown or use unsupported rules. Confirm them with the venue; ticket availability is unknown.")
        return scheduled, routes, warnings
