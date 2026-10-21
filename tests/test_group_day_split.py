"""Day-split group planning; fixture providers, fake hotels and fake AI only."""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from agents.group_day_split_agent import GroupDaySplitAgent, middle_pace
from api.main import app
from models.group_trip import GroupMemberPreferences, GroupTrip, GroupTripCreate
from models.hotels import HotelSuggestion, HotelSuggestions
from services.group_trip_service import GroupTripService, member_names
from services.group_trip_store import GroupTripStore
from services.local_llm import LocalModelError
from tests.test_group_trip import NOW, GroupFixtureProviders


class FakeHotels:
    def __init__(self, price=1200):
        self.price, self.searches = price, []

    def suggest(self, search):
        self.searches.append(search)
        rows = [HotelSuggestion(id="h1", name="Budget Stay", price_per_night=self.price, price_basis="ai_estimate"),
                HotelSuggestion(id="h2", name="Grand Hotel", price_per_night=self.price * 5, price_basis="ai_estimate")]
        return HotelSuggestions(destination=search.destination, check_in=search.check_in, check_out=search.check_out,
            nights=search.nights, adults=search.adults, rooms=search.rooms, currency=search.currency,
            suggestions=rows if self.price else [])


def ai_says(text=None, error=False):
    calls = []
    def enrich(system, user):
        calls.append(user)
        if error:
            raise LocalModelError("Gemini returned HTTP 429.")
        return {"why": text}
    enrich.calls = calls
    return enrich


MEMBERS = [
    ("Asha", GroupMemberPreferences(budget=100, interests=["beach", "food"], pace="relaxed")),
    ("Ravi", GroupMemberPreferences(budget=500, interests=["trek", "nature"], pace="packed")),
    ("Meera", GroupMemberPreferences(budget=1000, interests=["history"], pace="moderate")),
]


def planned(tmp_path, days=3, members=MEMBERS, hotels=None, enrich=None, ai=False):
    agent = GroupDaySplitAgent(GroupFixtureProviders(), hotels=hotels or FakeHotels(),
                               enrich=enrich or ai_says("unused"), ai_enabled=lambda: ai)
    original_run = agent.run
    agent.run = lambda group: original_run(group, NOW)
    service = GroupTripService(GroupTripStore(tmp_path / "groups.sqlite3"), agent)
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22", number_of_days=days,
        member_count=len(members), currency="INR", member_names=[name for name, _ in members]))
    for member, (_, preferences) in zip(group.members, members):
        group = service.member_preferences(group.id, member.id, group.version, preferences)
    return service.generate(group.id, group.version)


def test_each_member_gets_a_themed_day_at_their_own_pace(tmp_path):
    plan = planned(tmp_path).plan
    assert [(d.themes, d.featured_members, d.pace) for d in plan.day_plans] == [
        (["beach"], ["Asha"], "relaxed"), (["trek"], ["Ravi"], "packed"), (["history"], ["Meera"], "moderate")]
    by_day = {}
    for activity in plan.itinerary.activities:
        by_day.setdefault(activity.date.isoformat(), []).append(activity.place.id)
    assert "beach" in by_day["2026-10-22"] and "trek" in by_day["2026-10-23"] and "history" in by_day["2026-10-24"]
    assert "trek" not in by_day["2026-10-22"]  # reserved for Ravi's day
    # Ravi's second interest (nature) is also met by the shared garden.
    assert [c.covered_interests for c in plan.member_coverage] == [["beach"], ["trek", "nature"], ["history"]]
    assert plan.itinerary.valid and plan.itinerary.agents["group_fairness"] == "day split"


def test_conflicts_are_resolved_by_splitting_days(tmp_path):
    plan = planned(tmp_path).plan
    kinds = {c.conflict_type: c for c in plan.conflicts}
    interest = [c for c in plan.conflicts if c.conflict_type == "interests"]
    assert len(interest) == 3 and all(c.resolved for c in interest)
    asha_ravi = next(c for c in interest if c.members == ["Asha", "Ravi"])
    assert asha_ravi.resolution.endswith("Asha: Day 1 (beach); Ravi: Day 2 (trek).")
    assert "Day 1 relaxed, Day 2 packed, Day 3 moderate" in kinds["pace"].resolution
    assert "cheapest suggested hotel (Budget Stay)" in kinds["budget"].resolution


def test_more_themes_than_days_share_days_with_a_middle_pace(tmp_path):
    plan = planned(tmp_path, days=2).plan
    assert [(d.themes, d.pace) for d in plan.day_plans] == [(["beach", "history"], "moderate"), (["trek"], "packed")]
    assert all(c.covered_interests for c in plan.member_coverage)


def test_shared_top_interest_shares_a_day_and_second_interests_fill_spare_days(tmp_path):
    members = [("A", GroupMemberPreferences(interests=["beach", "history"], pace="relaxed")),
               ("B", GroupMemberPreferences(interests=["beaches"], pace="relaxed"))]
    plan = planned(tmp_path, days=3, members=members).plan
    assert [(d.themes, d.featured_members) for d in plan.day_plans] == [(["beach"], ["A", "B"]), (["history"], ["A"]), ([], [])]
    assert "Shared day" in plan.day_plans[2].note


def test_approximate_stay_cost_and_member_flags(tmp_path):
    hotels = FakeHotels(price=1200)
    plan = planned(tmp_path, hotels=hotels).plan
    costs = plan.approximate_costs
    assert hotels.searches[0].rooms == 2 and hotels.searches[0].nights == 2 and hotels.searches[0].adults == 3
    assert (costs.hotel_name, costs.stay_total, costs.stay_per_member) == ("Budget Stay", 4800, 1600)
    # The fixture's known hotel quote already covers accommodation, so it is not added twice.
    assert costs.approximate_total == plan.budget.known_total
    assert [c.status for c in costs.member_checks] == ["over", "over", "over"]
    assert plan.budget.known_total == 900  # existing budget left unchanged


def test_no_priced_hotels_means_no_approximate_costs(tmp_path):
    assert planned(tmp_path, hotels=FakeHotels(price=0)).plan.approximate_costs is None


def test_ai_writes_the_why_note_and_falls_back_to_rules(tmp_path):
    enrich = ai_says("Asha gets a calm beach day, Ravi a packed trek day and Meera a history day, so everyone wins.")
    plan = planned(tmp_path, enrich=enrich, ai=True).plan
    assert plan.why_source == "ai" and plan.why_this_plan.startswith("Asha gets")
    assert '"Ravi"' in enrich.calls[0] and "packed" in enrich.calls[0]
    fallback = planned(tmp_path / "b", enrich=ai_says(error=True), ai=True).plan
    assert fallback.why_source == "rules" and "Day 1 is Asha" in fallback.why_this_plan
    assert planned(tmp_path / "c", enrich=ai_says("short"), ai=True).plan.why_source == "rules"


def test_member_names_are_optional_trimmed_and_distinct():
    request = GroupTripCreate(destination="Goa", member_count=4, member_names=[" Asha ", "", "asha"])
    assert member_names(request) == ["Asha", "Member 2", "asha (2)", "Member 4"]
    assert member_names(GroupTripCreate(destination="Goa", member_count=2)) == ["Member 1", "Member 2"]
    with pytest.raises(ValueError):
        GroupTripCreate(destination="Goa", member_count=2, member_names=["x" * 81])


def test_plans_saved_before_this_change_still_load():
    legacy = {"id": "g", "version": 3, "destination": "Jaipur", "start_date": "2026-10-22", "number_of_days": 2,
              "member_count": 2, "currency": "INR", "members": [], "created_at": "x", "updated_at": "x",
              "plan": {"itinerary": {}, "why_this_plan": "old", "budget": {"currency": "INR", "known_total": 0,
                                                                          "known_per_member": 0}}}
    group = GroupTrip.model_validate(legacy)
    assert group.plan.day_plans == [] and group.plan.why_source == "rules" and group.plan.approximate_costs is None


def test_pace_median_helper():
    assert middle_pace([0, 2]) == "moderate"
    assert middle_pace([2, 2]) == "packed"
    assert middle_pace([0, 0, 2]) == "relaxed"


def test_api_accepts_member_names(tmp_path, monkeypatch):
    service = GroupTripService(GroupTripStore(tmp_path / "api.sqlite3"),
                               GroupDaySplitAgent(GroupFixtureProviders(), hotels=FakeHotels(), ai_enabled=lambda: False))
    monkeypatch.setattr(app.state, "group_trip_service", service, raising=False)
    with TestClient(app) as client:
        response = client.post("/group-trips", json={"destination": "Jaipur", "start_date": "2026-10-22",
            "number_of_days": 2, "member_count": 2, "currency": "INR", "member_names": ["Asha", "Ravi"]})
        assert response.status_code == 201
        assert [m["name"] for m in response.json()["members"]] == ["Asha", "Ravi"]


class RainyFirstDay(GroupFixtureProviders):
    def weather(self, preferences, latitude, longitude):
        days, source = super().weather(preferences, latitude, longitude)
        days[0].avoid_outdoor = True
        return days, source


def plan_with(providers, tmp_path, members=MEMBERS, days=3):
    agent = GroupDaySplitAgent(providers, hotels=FakeHotels(), ai_enabled=lambda: False)
    service = GroupTripService(GroupTripStore(tmp_path / "w.sqlite3"), agent)
    original = agent.run
    agent.run = lambda group: original(group, NOW)
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22", number_of_days=days,
        member_count=len(members), currency="INR", member_names=[name for name, _ in members]))
    for member, (_, preferences) in zip(group.members, members):
        group = service.member_preferences(group.id, member.id, group.version, preferences)
    return service.generate(group.id, group.version).plan


def test_rainy_day_gets_the_indoor_theme_and_the_beach_day_moves(tmp_path):
    plan = plan_with(RainyFirstDay(), tmp_path)
    themes = {d.day_number: (d.themes, d.featured_members) for d in plan.day_plans}
    assert themes[1] == (["history"], ["Meera"])  # the museum is indoors
    assert "rain forecast" in plan.day_plans[0].note
    assert any("outdoor-focused days were moved" in w for w in plan.itinerary.warnings)
    scheduled = {a.place.id: a.date.isoformat() for a in plan.itinerary.activities}
    assert scheduled["history"] == "2026-10-22" and scheduled["beach"] != "2026-10-22"
    assert all(c.covered_interests for c in plan.member_coverage)


def test_theme_without_places_falls_back_to_the_members_next_interest(tmp_path):
    members = [("Asha", GroupMemberPreferences(interests=["beach"], pace="relaxed")),
               ("Ravi", GroupMemberPreferences(interests=["skydiving", "garden"], pace="packed"))]
    plan = plan_with(GroupFixtureProviders(), tmp_path, members=members, days=2)
    assert [(d.themes, d.featured_members) for d in plan.day_plans] == [(["beach"], ["Asha"]), (["garden"], ["Ravi"])]
    assert any("No nearby places matched “skydiving”" in w for w in plan.itinerary.warnings)
    assert "garden" in plan.day_plans[1].note
