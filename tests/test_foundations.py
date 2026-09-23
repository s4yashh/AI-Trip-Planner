import json

import httpx
import pytest

from models.live import Preferences, Trip
from services.local_llm import LocalLLM, LocalModelError
from services.trip_store import ConflictError, TripStore


def test_store_restart_and_atomic_conflict(tmp_path):
    path = tmp_path / "trips.db"
    store = TripStore(path)
    trip = store.create(Trip(preferences=Preferences(destination="Rome")))
    changed = store.get(trip.id)
    changed.preferences.budget = 100
    saved = store.save(changed, 1, "Budget updated")
    assert saved.version == 2
    with pytest.raises(ConflictError):
        store.save(trip, 1, "Stale write")
    restarted = TripStore(path)
    assert restarted.get(trip.id).preferences.budget == 100
    assert restarted.history(trip.id)[0]["before"]["preferences"]["budget"] is None


def llm(monkeypatch, content):
    monkeypatch.setenv("LOCAL_LLM_MODEL", "already-loaded")
    def respond(request):
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(200, json={"choices": [{"message": {"content": content}}]})
    return LocalLLM(httpx.Client(transport=httpx.MockTransport(respond)))


def test_model_extracts_valid_preferences(monkeypatch):
    model = llm(monkeypatch, json.dumps({"explanation": "A slower pace", "preference_changes": {"pace": "relaxed"}}))
    assert model.chat("Go slower", Preferences(destination="Rome")).preference_changes == {"pace": "relaxed"}


@pytest.mark.parametrize("result", ["not json", '{"explanation":"x","preference_changes":{"number_of_days":0}}',
    '{"explanation":"x","preference_changes":{"allowances":{"food":50}}}',
    '{"explanation":"x","referenced_place_ids":["invented"]}'])
def test_model_rejects_invalid_or_invented_data(monkeypatch, result):
    with pytest.raises(LocalModelError):
        llm(monkeypatch, result).chat("plan", Preferences(destination="Rome"))


def test_model_missing_and_connection_error(monkeypatch):
    monkeypatch.delenv("LOCAL_LLM_MODEL", raising=False)
    with pytest.raises(LocalModelError, match="LOCAL_LLM_MODEL"):
        LocalLLM().chat("Hello")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "existing")
    def offline(request):
        raise httpx.ConnectError("offline", request=request)
    with pytest.raises(LocalModelError, match="Cannot connect"):
        LocalLLM(httpx.Client(transport=httpx.MockTransport(offline))).chat("Hello")
