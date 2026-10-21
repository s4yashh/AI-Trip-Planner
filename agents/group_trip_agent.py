"""Fair group recommendation and itinerary planning using live trip services."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from statistics import median

from agents.live_agents import (AccommodationAgent, AdaptiveItineraryAgent, EmergencyAgent,
    LiveBudgetAgent, LiveRestaurantAgent, LiveWeatherAgent, RecommendationAgent, TrafficAgent,
    TransportationAgent)
from models.group_trip import (GroupBudget, GroupConflict, GroupPlan, GroupTrip, MemberBudgetCheck,
    MemberCoverage)
from models.live import LivePlan, Preferences, Source
from services.live_providers import LiveProviders, ProviderError
from utils.text_features import TfidfVectorizer, cosine_similarity, tokenize
from validation.live_validator import LiveTripValidator


GROUP_INTEREST_SYNONYMS = {
    "beach": ["beaches", "coast", "coastal", "shore", "seaside", "ocean"],
    "trek": ["trekking", "hike", "hiking", "trail", "mountain"],
    "history": ["historical", "historic", "heritage", "fort", "monument"],
    "architecture": ["architectural", "building", "palace", "fort"],
    "culture": ["cultural", "heritage", "traditional", "temple"],
    "nature": ["natural", "park", "garden", "forest", "lake"],
    "food": ["cuisine", "restaurant", "cafe", "market"],
    "adventure": ["adventurous", "trek", "trekking", "hike", "hiking"],
    "shopping": ["shop", "market", "bazaar"],
}

PACE_LEVEL = {"relaxed": 0, "moderate": 1, "packed": 2}
PACE_FROM_LEVEL = {0: "relaxed", 1: "moderate", 2: "packed"}
DAILY_ACTIVITY_COUNT = {"relaxed": 2, "moderate": 3, "packed": 5}
LIVE_PACE = {"relaxed": "relaxed", "moderate": "balanced", "packed": "busy"}


class GroupTripAgent:
    """Build one schedule while reserving coverage for each member's top interests."""

    def __init__(self, providers=None):
        self.providers = providers or LiveProviders()
        self.validator = LiveTripValidator()

    def run(self, group: GroupTrip, now=None) -> GroupPlan:
        now = now or datetime.now(timezone.utc)
        preferences = self._combined_preferences(group)
        plan = LivePlan()
        try:
            location, source = self.providers.geocode(group.destination)
            plan.sources["destination"] = source
            plan.timezone = location.get("timezone") or "UTC"
        except (ProviderError, ValueError, KeyError) as exc:
            plan.sources["destination"] = Source(provider="Open-Meteo geocoding", message=str(exc))
            plan.conflicts = [str(exc)]
            plan.budget = LiveBudgetAgent().run((preferences, [], []))
            return self._summarize(group, plan)

        tasks = {
            "places": lambda: self.providers.discover(location["latitude"], location["longitude"]),
            "weather": lambda: LiveWeatherAgent(self.providers).run((preferences, location)),
            "accommodation": lambda: AccommodationAgent(self.providers).run((preferences, location)),
        }
        results = {}
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = {name: pool.submit(task) for name, task in tasks.items()}
            for name, future in futures.items():
                try:
                    values, source = future.result()
                    results[name] = values
                    plan.sources[name] = source
                    plan.agents[name] = "complete" if values else "no results"
                    if source.message:
                        plan.warnings.append(source.message)
                except (ProviderError, ValueError, KeyError, TypeError) as exc:
                    results[name] = []
                    plan.sources[name] = Source(provider=name, message=str(exc))
                    plan.agents[name] = "unavailable"
                    plan.warnings.append(str(exc))

        all_places = results["places"]
        recommended = RecommendationAgent().run((preferences, all_places))
        plan.restaurants = LiveRestaurantAgent().run((preferences, all_places))
        place_ids = {place.id for place in recommended}
        plan.places = recommended + [place for place in plan.restaurants if place.id not in place_ids]
        plan.lodging = [place for place in all_places if place.kind == "lodging"][:12]
        plan.emergency = EmergencyAgent().run(all_places)
        plan.weather = results["weather"]
        plan.hotels = results["accommodation"]
        plan.budget = LiveBudgetAgent().run((preferences, plan.hotels, []))
        if not plan.budget.complete:
            plan.warnings.append("Group cost data is incomplete; known costs are shown as a lower bound.")

        for name, values in (("poi_recommendation", recommended), ("restaurant", plan.restaurants),
                             ("emergency", plan.emergency)):
            plan.agents[name] = "complete" if values else (
                "unavailable" if plan.sources.get("places", Source(provider="places")).status == "unavailable"
                else "no results")

        candidates, member_scores = self._fair_candidates(plan.places, group.members, preferences)
        transport = TransportationAgent(self.providers)
        scheduler = AdaptiveItineraryAgent(transport)
        try:
            plan.activities, plan.routes, notes = scheduler.run(
                (preferences, candidates, plan.weather, [], plan.timezone, now))
            plan.warnings = list(dict.fromkeys(plan.warnings + notes))
            plan.agents["itinerary"] = "complete"
            plan.agents["transportation"] = (
                "complete" if any(route.source.status in {"live", "cached"} for route in plan.routes)
                else "estimated")
        except (ProviderError, ValueError, KeyError) as exc:
            plan.conflicts = [f"Scheduling unavailable: {exc}"]
            plan.agents["itinerary"] = "unavailable"

        plan.conflicts = list(dict.fromkeys(plan.conflicts + self.validator.validate_live(preferences, plan)))
        plan.agents["validator"] = "passed" if not plan.conflicts else "conflict"
        plan.agents["orchestrator"] = "complete" if not plan.conflicts and bool(plan.activities) else "conflict"
        plan.agents["group_fairness"] = "complete"
        plan.valid = not plan.conflicts and bool(plan.activities)
        plan.attempts = 1
        plan.generated_at = datetime.now(timezone.utc).isoformat()
        plan.sources["traffic"] = TrafficAgent().run(plan.routes)
        plan.agents["traffic"] = plan.sources["traffic"].status
        return self._summarize(group, plan, member_scores)

    @staticmethod
    def _combined_preferences(group):
        members = [member for member in group.members if member.preferences is not None]
        paces = sorted(PACE_LEVEL[member.preferences.pace] for member in members)
        median_level = int(median(paces))
        # When two paces fall between levels, choose the more balanced compromise.
        if len(paces) % 2 == 0:
            middle = len(paces) // 2
            median_level = paces[middle] if paces[middle - 1] == paces[middle] else 1
        pace = PACE_FROM_LEVEL[median_level]
        interests = list(dict.fromkeys(
            interest for member in members for interest in member.preferences.interests))[:20]
        return Preferences(
            destination=group.destination,
            start_date=group.start_date,
            number_of_days=group.number_of_days,
            currency=group.currency,
            interests=interests,
            travelers=group.member_count,
            rooms=group.member_count,
            pace=LIVE_PACE[pace],
        )

    @staticmethod
    def _place_text(place):
        return " ".join([place.kind, place.name, *place.tags.values()]).lower()

    @staticmethod
    def _interest_text(interest):
        key = interest.strip().lower()
        family = topic_family(key)
        aliases = GROUP_INTEREST_SYNONYMS.get(family, [])
        return " ".join([key, family, *aliases])

    def _fair_candidates(self, places, members, preferences):
        if not places:
            return [], {}
        documents = [self._place_text(place) for place in places]
        interest_queries = {
            (member.id, interest): self._interest_text(interest)
            for member in members if member.preferences
            for interest in member.preferences.interests
        }
        vectorizer = TfidfVectorizer().fit([*documents, *interest_queries.values()])
        place_vectors = vectorizer.transform(documents)
        interest_vectors = {key: vectorizer.transform([query])[0]
                            for key, query in interest_queries.items()}

        scores = {}
        matched_interests = {}
        for member in members:
            prefs = member.preferences
            if prefs is None:
                continue
            for place, vector in zip(places, place_vectors):
                interest_scores = [
                    (interest, cosine_similarity(interest_vectors[(member.id, interest)], vector))
                    for interest in prefs.interests
                ]
                weighted = [(score * (2 if index == 0 else 1))
                            for index, (_, score) in enumerate(interest_scores)]
                scores[(member.id, place.id)] = sum(weighted) / max(
                    1, sum(2 if index == 0 else 1 for index in range(len(weighted))))
                matched_interests[(member.id, place.id)] = [
                    interest for interest, score in interest_scores if score > 0]

        capacity = group_capacity(preferences.number_of_days, preferences.pace)
        selected = []
        remaining = list(places)
        uncovered = {member.id for member in members if member.preferences and member.preferences.interests}
        while remaining and len(selected) < capacity:
            def rank(place):
                newly_covered = {member_id for member_id in uncovered
                                 if matched_interests.get((member_id, place.id))}
                total_score = sum(scores.get((member.id, place.id), 0) for member in members)
                return (-len(newly_covered), -total_score, -place.score, place.id)

            place = min(remaining, key=rank)
            selected.append(place)
            uncovered -= {member_id for member_id in uncovered
                          if matched_interests.get((member_id, place.id))}
            remaining.remove(place)
        return selected, scores

    def _summarize(self, group, plan, member_scores=None):
        member_scores = member_scores or {}
        coverage = []
        for member in group.members:
            prefs = member.preferences
            top = prefs.interests[:2] if prefs else []
            found = []
            if prefs:
                for interest in top:
                    if any(member_scores.get((member.id, activity.place.id), 0) > 0
                           and interest in self._matched_for(member, activity.place)
                           for activity in plan.activities):
                        found.append(interest)
            coverage.append(MemberCoverage(member_id=member.id, member_name=member.name,
                                           top_interests=top, covered_interests=found))

        budget = self._group_budget(group, plan)
        conflicts = self._group_conflicts(group, coverage, budget)
        pace = self._combined_preferences(group).pace
        why = (f"Used a {pace} group pace (the median compromise), reserved activity slots for each member's "
               "highest-ranked interests, then filled remaining slots with the strongest group matches. "
               "Shared costs are split equally for the per-member estimate.")
        return GroupPlan(itinerary=plan, why_this_plan=why, member_coverage=coverage,
                         conflicts=conflicts, budget=budget)

    def _matched_for(self, member, place):
        # Recompute interest-level matches for final scheduled activities so the
        # displayed coverage reflects the itinerary, not just candidate ranking.
        place_tokens = set(tokenize(self._place_text(place)))
        matched = []
        if not member.preferences:
            return matched
        for interest in member.preferences.interests:
            query_tokens = set(tokenize(self._interest_text(interest)))
            if query_tokens & place_tokens:
                matched.append(interest)
        return matched

    @staticmethod
    def _group_budget(group, plan):
        count = max(1, group.member_count)
        known_share = round(plan.budget.known_total / count, 2)
        complete = plan.budget.complete
        total = plan.budget.total if complete else None
        estimate_per_member = round(total / count, 2) if total is not None else None
        checks = []
        for member in group.members:
            cap = member.preferences.budget if member.preferences else None
            share = estimate_per_member if complete else known_share
            if cap is None:
                status, note = "unknown", "No personal budget cap was entered."
            elif share > cap:
                status = "over"
                note = ("Estimated equal share exceeds this member's budget." if complete else
                        "Known costs alone exceed this member's budget; unknown costs remain.")
            elif complete:
                status, note = "within", "Estimated equal share is within this member's budget."
            else:
                status, note = "unknown", "Known-cost share is below the cap, but the full trip estimate is incomplete."
            checks.append(MemberBudgetCheck(member_id=member.id, member_name=member.name,
                budget=cap, known_share=share, status=status, note=note))
        return GroupBudget(currency=group.currency, total_estimate=total, known_total=plan.budget.known_total,
            estimated_per_member=estimate_per_member, known_per_member=known_share,
            estimate_complete=complete, member_checks=checks)

    @staticmethod
    def _group_conflicts(group, coverage, budget):
        conflicts = []
        covered = {item.member_id: bool(item.covered_interests) for item in coverage}
        for index, first in enumerate(group.members):
            if not first.preferences:
                continue
            first_topics = {topic_family(interest) for interest in first.preferences.interests}
            for second in group.members[index + 1:]:
                if not second.preferences:
                    continue
                second_topics = {topic_family(interest) for interest in second.preferences.interests}
                if first_topics & second_topics:
                    continue
                resolved = covered.get(first.id, False) and covered.get(second.id, False)
                conflicts.append(GroupConflict(
                    conflict_type="interests", members=[first.name, second.name],
                    description=(f"{first.name} and {second.name} prioritize different interests: "
                                 f"{', '.join(first.preferences.interests[:2])} vs "
                                 f"{', '.join(second.preferences.interests[:2])}."),
                    resolution=("Scheduled interest-matched activities for both members in a fair rotation."
                                if resolved else "Rotated available activities, but live place data did not cover both members' top interests."),
                    resolved=resolved,
                ))

        pace_levels = [PACE_LEVEL[member.preferences.pace] for member in group.members if member.preferences]
        if len(set(pace_levels)) > 1:
            chosen = GroupTripAgent._combined_preferences(group).pace
            conflicts.append(GroupConflict(conflict_type="pace", members=[m.name for m in group.members],
                description="Members requested different daily paces.",
                resolution=f"Used a {chosen} pace as the median compromise for the shared itinerary.",
                resolved=True))

        caps = [member.preferences.budget for member in group.members
                if member.preferences and member.preferences.budget is not None]
        if len(caps) >= 2 and max(caps) > min(caps) * 1.5:
            resolved = all(check.status == "within" for check in budget.member_checks
                           if check.budget is not None)
            conflicts.append(GroupConflict(conflict_type="budget", members=[m.name for m in group.members],
                description="Members have substantially different personal budget caps.",
                resolution=("Compared an equal share of the known trip estimate against each member's cap."
                            if budget.estimate_complete else
                            "Compared the known-cost share against each cap; missing prices remain unknown and are not treated as affordable."),
                resolved=resolved))
        return conflicts


def group_capacity(number_of_days, pace):
    daily_count = DAILY_ACTIVITY_COUNT.get(pace, {"balanced": 3, "busy": 5}.get(pace, 3))
    return number_of_days * daily_count


def topic_family(interest):
    value = interest.strip().lower()
    for family, aliases in GROUP_INTEREST_SYNONYMS.items():
        if value == family or value in aliases:
            return family
    return " ".join(tokenize(value))
