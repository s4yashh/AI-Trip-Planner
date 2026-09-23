"""Live API contracts: test providers are explicitly injected at the service boundary."""
import pytest
from fastapi.testclient import TestClient

from api.main import app
from agents.live_orchestrator import LiveOrchestrator
from services.trip_service import TripService
from services.trip_store import TripStore
from tests.test_live_planning import FixtureProviders, NOW


@pytest.fixture
def api(tmp_path, monkeypatch):
    service = TripService(TripStore(tmp_path / "api.db"), LiveOrchestrator(FixtureProviders()), clock=lambda: NOW)
    monkeypatch.setattr(app.state, "service", service, raising=False)
    with TestClient(app) as client:
        yield client, service


def payload(**changes):
    data = {"destination": "Jaipur", "number_of_days": 2, "start_date": "2026-10-02", "currency": "INR"}
    data.update(changes)
    return data


def test_create_read_edit_and_conflict(api):
    client, service = api
    response = client.post("/trips", json=payload())
    assert response.status_code == 201
    trip = response.json()
    assert trip["plan"]["valid"]
    assert trip["plan"]["budget"]["total"] is None
    assert client.get("/trips").json()[0]["id"] == trip["id"]
    assert client.get("/trips/"+trip["id"]).json() == trip
    path = "/trips/"+trip["id"]
    changed = client.patch(path, json={"version": 1, "monitoring": False})
    assert changed.status_code == 200
    assert changed.json()["monitoring"] is False
    assert client.patch(path, json={"version": 1, "monitoring": True}).status_code == 409
    assert len(client.get(path+"/revisions").json()) == 2


@pytest.mark.parametrize("changes", [{"number_of_days": 0}, {"budget": -5}, {"currency": "EUR"},
    {"start_date": "bad-date"}, {"destination": " "}, {"travelers": 0}, {"allowances": {"food": -1}}])
def test_bad_inputs_rejected(api, changes):
    assert api[0].post("/trips", json=payload(**changes)).status_code == 422


def test_legacy_route_preserves_shape_without_fake_prices(api):
    response = api[0].post("/trip", json=payload())
    assert response.status_code == 200
    result = response.json()
    assert result["trip_summary"]["destination"] == "Jaipur"
    assert result["recommended_pois"][0]["estimated_cost"] is None
    assert len(result["itinerary"]["days"]) == 2
    assert result["budget_analysis"]["total_cost"] is None


def test_expenses_activity_controls_and_currency_lock(api):
    client, service = api
    trip = client.post("/trips", json=payload()).json()
    path = "/trips/"+trip["id"]
    activity_id = trip["plan"]["activities"][0]["id"]
    locked = client.patch(path+"/activities/"+activity_id, json={"version": 1, "locked": True, "committed": True})
    assert locked.status_code == 200
    expense = client.post(path+"/expenses", json={"version": 2, "expense": {"category": "food", "amount": 200, "description": "Lunch"}})
    assert expense.status_code == 200
    assert expense.json()["plan"]["budget"]["spent"] == 200
    assert expense.json()["plan"]["activities"][0]["committed"]
    assert client.patch(path, json={"version": 3, "preferences": payload(currency="USD")}).status_code == 409


def test_missing_local_model_leaves_trip_unchanged(api, monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_MODEL", raising=False)
    client, service = api
    trip = client.post("/trips", json=payload()).json()
    path = "/trips/"+trip["id"]
    assert client.post(path+"/chat", json={"version": 1, "message": "Go slower"}).status_code == 503
    assert client.get(path).json()["version"] == 1
    assert client.get("/health").status_code == 200
    assert client.get("/capabilities").json()["local_model"]["configured"] is False


def test_unknown_trip_and_foreign_origin(api):
    client, _ = api
    assert client.get("/trips/missing").status_code == 404
    assert client.post("/trips", json=payload(), headers={"Origin": "https://another.example"}).status_code == 403
