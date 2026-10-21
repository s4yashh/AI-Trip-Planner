from datetime import timedelta, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from agents.group_trip_agent import GroupTripAgent
from api.main import app
from models.group_trip import GroupMemberPreferences, GroupTripCreate
from models.live import HotelOffer, Place, Route, Source, WeatherDay
from services.group_trip_service import GroupTripService
from services.group_trip_store import GroupTripConflict, GroupTripStore
from services.trip_service import TripService
from services.trip_store import TripStore


NOW = datetime(2026, 10, 21, 8, tzinfo=timezone.utc)


class GroupFixtureProviders:
    def geocode(self, destination):
        return {"latitude": 26.9, "longitude": 75.8, "timezone": "UTC"}, Source(provider="Fixture geocoder", status="live")

    def discover(self, latitude, longitude):
        places = [
            Place(id="beach", name="Blue Beach", kind="beach", latitude=26.91, longitude=75.8,
                  opening_hours="09:00-17:00", source=Source(provider="Fixture places", status="live")),
            Place(id="trek", name="Mountain Trek Trail", kind="trail", latitude=26.92, longitude=75.8,
                  opening_hours="09:00-17:00", source=Source(provider="Fixture places", status="live")),
            Place(id="history", name="Old History Museum", kind="museum", latitude=26.93, longitude=75.8,
                  opening_hours="09:00-17:00", source=Source(provider="Fixture places", status="live")),
            Place(id="garden", name="Shared City Garden", kind="park", latitude=26.94, longitude=75.8,
                  opening_hours="09:00-17:00", source=Source(provider="Fixture places", status="live")),
        ]
        return places, Source(provider="Fixture places", status="live")

    def weather(self, preferences, latitude, longitude):
        weather = [WeatherDay(date=preferences.start_date + timedelta(days=offset), avoid_outdoor=False)
                   for offset in range(preferences.number_of_days)]
        return weather, Source(provider="Fixture weather", status="live")

    def hotels(self, preferences, latitude, longitude):
        offer = HotelOffer(id="offer", hotel_id="hotel", name="Group hotel", amount=900,
            currency=preferences.currency, check_in=preferences.start_date,
            check_out=preferences.start_date + timedelta(days=max(1, preferences.number_of_days - 1)),
            rooms=preferences.rooms, source=Source(provider="Fixture hotel", status="live"))
        return [offer], Source(provider="Fixture hotel", status="live")

    def route(self, first, second, mode, departure):
        return Route(from_id=first.id, to_id=second.id, minutes=10, distance_km=1,
                     source=Source(provider="Fixture route", status="live"))


def fill_members(service, group):
    members = [
        GroupMemberPreferences(budget=100, interests=["beach"], pace="relaxed"),
        GroupMemberPreferences(budget=500, interests=["trek"], pace="packed"),
        GroupMemberPreferences(budget=1000, interests=["history"], pace="moderate"),
    ]
    for member, preferences in zip(group.members, members):
        group = service.member_preferences(group.id, member.id, group.version, preferences)
    return group


def make_service(path):
    return GroupTripService(GroupTripStore(path), GroupTripAgent(GroupFixtureProviders()))


def test_group_planner_fairly_covers_members_and_flags_budget_conflicts(tmp_path):
    service = make_service(tmp_path / "groups.sqlite3")
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22",
        number_of_days=3, member_count=3, currency="INR"))
    group = fill_members(service, group)

    saved = service.generate(group.id, group.version)
    plan = saved.plan

    assert plan is not None
    assert plan.itinerary.activities
    assert [item.covered_interests for item in plan.member_coverage] == [["beach"], ["trek"], ["history"]]
    assert "median compromise" in plan.why_this_plan
    assert plan.budget.known_total == 900
    assert plan.budget.known_per_member == 300
    assert plan.budget.member_checks[0].status == "over"
    assert any(conflict.conflict_type == "pace" for conflict in plan.conflicts)
    assert any(conflict.conflict_type == "interests" and conflict.resolved for conflict in plan.conflicts)
    assert any(conflict.conflict_type == "budget" and not conflict.resolved for conflict in plan.conflicts)


def test_group_database_is_separate_and_expected_version_is_enforced(tmp_path):
    path = tmp_path / "group.sqlite3"
    service = make_service(path)
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22",
        number_of_days=2, member_count=2, currency="INR"))
    first_member = group.members[0]
    changed = service.member_preferences(group.id, first_member.id, group.version,
        GroupMemberPreferences(interests=["history"], pace="moderate"))

    with pytest.raises(GroupTripConflict, match="Group trip changed"):
        service.member_preferences(group.id, group.members[1].id, group.version,
            GroupMemberPreferences(interests=["food"], pace="relaxed"))

    restarted = GroupTripStore(path)
    assert restarted.get(group.id).members[0].preferences.interests == ["history"]
    assert changed.version == 2


def test_group_api_create_save_members_and_generate(tmp_path, monkeypatch):
    group_service = make_service(tmp_path / "api-groups.sqlite3")
    single_service = TripService(TripStore(tmp_path / "single-trips.sqlite3"), clock=lambda: NOW)
    monkeypatch.setattr(app.state, "group_trip_service", group_service, raising=False)
    monkeypatch.setattr(app.state, "service", single_service, raising=False)

    with TestClient(app) as client:
        created = client.post("/group-trips", json={
            "destination": "Jaipur", "start_date": "2026-10-22", "number_of_days": 3,
            "member_count": 3, "currency": "INR",
        })
        assert created.status_code == 201
        group = created.json()
        for member, interests in zip(group["members"], (["beach"], ["trek"], ["history"])):
            response = client.patch(f"/group-trips/{group['id']}/members/{member['id']}", json={
                "version": group["version"],
                "preferences": {"budget": 500, "interests": interests, "pace": "moderate"},
            })
            assert response.status_code == 200
            group = response.json()
        generated = client.post(f"/group-trips/{group['id']}/plan", json={"version": group["version"]})
        assert generated.status_code == 200
        assert generated.json()["plan"]["itinerary"]["activities"]
        assert client.get(f"/group-trips/{group['id']}").status_code == 200
        assert client.get("/trips").json() == []


def test_group_plan_requires_preferences_from_every_member(tmp_path):
    service = make_service(tmp_path / "groups.sqlite3")
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22",
        number_of_days=2, member_count=2, currency="INR"))
    with pytest.raises(ValueError, match="every member"):
        service.generate(group.id, group.version)


def test_food_interests_can_select_a_restaurant_activity(tmp_path):
    class FoodProviders(GroupFixtureProviders):
        def discover(self, latitude, longitude):
            cafe = Place(id="cafe", name="Local Food Cafe", kind="cafe", latitude=26.91, longitude=75.8,
                opening_hours="09:00-17:00", tags={"cuisine": "local food"},
                source=Source(provider="Fixture places", status="live"))
            return [cafe], Source(provider="Fixture places", status="live")

    service = GroupTripService(GroupTripStore(tmp_path / "food-groups.sqlite3"), GroupTripAgent(FoodProviders()))
    group = service.create(GroupTripCreate(destination="Jaipur", start_date="2026-10-22",
        number_of_days=2, member_count=2, currency="INR"))
    for member in group.members:
        group = service.member_preferences(group.id, member.id, group.version,
            GroupMemberPreferences(interests=["food"], pace="moderate"))

    result = service.generate(group.id, group.version).plan
    assert result is not None
    assert result.itinerary.activities[0].place.kind == "cafe"
    assert all(item.covered_interests == ["food"] for item in result.member_coverage)
