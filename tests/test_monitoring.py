from datetime import timedelta

import pytest

from agents.live_orchestrator import LiveOrchestrator
from services.trip_service import TripService
from services.trip_store import ConflictError, TripStore
from tests.test_live_planning import FixtureProviders, NOW, preferences


def test_monitor_resumes_from_database_and_records_automatic_revision(tmp_path):
    path = tmp_path / "trips.db"
    provider = FixtureProviders()
    service = TripService(TripStore(path), LiveOrchestrator(provider), clock=lambda: NOW)
    trip = service.create(preferences())
    before = [(a.id, a.date) for a in trip.plan.activities]
    provider.rain = True
    restarted = TripService(TripStore(path), LiveOrchestrator(provider), clock=lambda: NOW + timedelta(minutes=16))
    restarted.monitor_once()
    after = restarted.store.get(trip.id)
    assert after.version == 2
    assert after.plan.valid
    assert [(a.id, a.date) for a in after.plan.activities] != before
    assert "Automatic refresh" in restarted.store.history(trip.id)[0]["reason"]
    restarted.monitor_once()
    assert restarted.store.get(trip.id).version == 2


def test_failed_replan_retains_schedule_and_surfaces_conflict(tmp_path):
    provider = FixtureProviders()
    service = TripService(TripStore(tmp_path / "trips.db"), LiveOrchestrator(provider), clock=lambda: NOW)
    trip = service.create(preferences())
    outdoor = next(a for a in trip.plan.activities if a.place.kind == "park")
    trip = service.activity(trip.id, outdoor.id, trip.version, {"locked": True})
    before = [a.model_dump() for a in trip.plan.activities]
    provider.rain = True
    updated = service.replan(trip, "Manual refresh")
    assert [a.model_dump() for a in updated.plan.activities] == before
    assert not updated.plan.valid
    assert "Weather" in updated.monitoring_error


def test_concurrent_user_edit_wins_over_monitor(tmp_path):
    service = TripService(TripStore(tmp_path / "trips.db"), LiveOrchestrator(FixtureProviders()), clock=lambda: NOW)
    trip = service.create(preferences())
    stale = service.store.get(trip.id)
    service.update(trip.id, trip.version, monitoring=False)
    with pytest.raises(ConflictError):
        service.replan(stale, "Automatic refresh")
    assert service.store.get(trip.id).monitoring is False


def test_completed_activities_are_preserved_and_destination_change_rejected(tmp_path):
    service = TripService(TripStore(tmp_path / "trips.db"), LiveOrchestrator(FixtureProviders()), clock=lambda: NOW)
    trip = service.create(preferences())
    activity = trip.plan.activities[0]
    updated = service.activity(trip.id, activity.id, trip.version, {"completed": True})
    preserved = next(a for a in updated.plan.activities if a.id == activity.id)
    assert preserved.date == activity.date and preserved.start_time == activity.start_time
    changed = preferences().model_copy(update={"destination": "Tokyo"})
    with pytest.raises(ConflictError, match="protected"):
        service.update(trip.id, updated.version, preferences=changed)
