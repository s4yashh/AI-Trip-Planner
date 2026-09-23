"""Live-data extension of the orchestrator, with independent specialist agents."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from agents.orchestrator_agent import OrchestratorAgent
from agents.live_agents import (AccommodationAgent, AdaptiveItineraryAgent, EmergencyAgent,
    LiveBudgetAgent, LiveRestaurantAgent, LiveWeatherAgent, RecommendationAgent, TrafficAgent, TransportationAgent)
from models.live import LivePlan, Preferences, Source, utcnow
from services.live_providers import LiveProviders, ProviderError
from validation.live_validator import LiveTripValidator
from validation.trip_validator import MAX_REPLAN_ATTEMPTS


class LiveOrchestrator(OrchestratorAgent):
    """No dataset fallback. Each run owns its mutable scheduling state."""
    def __init__(self, providers=None):
        self.providers = providers or LiveProviders()
        self.validator = LiveTripValidator()

    def run(self, input_data, previous=None, expenses=(), now=None):
        prefs = Preferences.model_validate(input_data)
        now = now or datetime.now(timezone.utc)
        plan = LivePlan()
        old = previous.activities if previous else []
        try:
            location, source = self.providers.geocode(prefs.destination)
            plan.sources["destination"] = source
            plan.timezone = location.get("timezone") or "UTC"
        except (ProviderError, ValueError, KeyError) as exc:
            plan.sources["destination"] = Source(provider="Open-Meteo geocoding", message=str(exc))
            plan.conflicts = [str(exc)]
            plan.budget = LiveBudgetAgent().run((prefs, [], expenses))
            return plan

        def discover():
            return self.providers.discover(location["latitude"], location["longitude"])

        tasks = {"places": discover,
                 "weather": lambda: LiveWeatherAgent(self.providers).run((prefs, location)),
                 "accommodation": lambda: AccommodationAgent(self.providers).run((prefs, location))}
        results = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {name: pool.submit(task) for name, task in tasks.items()}
            for name, future in futures.items():
                try:
                    values, source = future.result()
                    results[name] = values
                    plan.sources[name] = source
                    plan.agents[name] = "complete" if values else "no results"
                except (ProviderError, ValueError, KeyError, TypeError) as exc:
                    results[name] = []
                    plan.sources[name] = Source(provider=name, message=str(exc))
                    plan.agents[name] = "unavailable"
                    plan.warnings.append(str(exc))
        all_places = results["places"]
        plan.places = RecommendationAgent().run((prefs, all_places))
        plan.restaurants = LiveRestaurantAgent().run((prefs, all_places))
        plan.lodging = [p for p in all_places if p.kind == "lodging"][:12]
        plan.emergency = EmergencyAgent().run(all_places)
        plan.weather, plan.hotels = results["weather"], results["accommodation"]
        for name, values in [("poi_recommendation", plan.places), ("restaurant", plan.restaurants), ("emergency", plan.emergency)]:
            plan.agents[name] = "complete" if values else "unavailable" if plan.sources["places"].status == "unavailable" else "no results"
        plan.budget = LiveBudgetAgent().run((prefs, plan.hotels, expenses))
        plan.agents["budget"] = "complete" if plan.budget.complete else "needs allowances"
        if not plan.budget.complete:
            plan.warnings.append("Budget is incomplete. Unknown category costs need traveler allowances; no within-budget guarantee is possible.")
        transport = TransportationAgent(self.providers)
        scheduler = AdaptiveItineraryAgent(transport)
        candidates = list(plan.places)
        for attempt in range(1, max(1, min(MAX_REPLAN_ATTEMPTS, 5))+1):
            plan.attempts = attempt
            try:
                plan.activities, plan.routes, notes = scheduler.run((prefs, candidates, plan.weather, old, plan.timezone, now))
                plan.warnings = list(dict.fromkeys(plan.warnings + notes))
                plan.agents["itinerary"] = "complete"
                plan.agents["transportation"] = "complete" if any(r.source.status in {"live", "cached"} for r in plan.routes) else "estimated"
            except (ProviderError, ValueError, KeyError) as exc:
                plan.conflicts = [f"Scheduling unavailable: {exc}"]
                plan.agents["itinerary"] = "unavailable"
                break
            plan.conflicts = self.validator.validate_live(prefs, plan, old)
            plan.agents["validator"] = "passed" if not plan.conflicts else "conflict"
            if not plan.conflicts:
                break
            # A conservative second attempt reduces density; never alters protected activities.
            removable = next((a for a in reversed(plan.activities) if not (a.locked or a.completed or a.committed)
                              and a.date >= now.astimezone(ZoneInfo(plan.timezone)).date()), None)
            if removable is None or plan.budget.within_budget is False:
                break
            candidates = [p for p in candidates if p.id != removable.place.id]
        plan.sources["traffic"] = TrafficAgent().run(plan.routes)
        plan.agents["traffic"] = plan.sources["traffic"].status
        plan.valid = not plan.conflicts and bool(plan.activities)
        plan.agents["orchestrator"] = "complete" if plan.valid else "conflict"
        plan.generated_at = utcnow()
        return plan
