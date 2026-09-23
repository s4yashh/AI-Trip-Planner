"""Gemini contract tests; dummy keys and mocked HTTP only."""
import json

import httpx
import pytest
from fastapi.testclient import TestClient

from api.main import app
from models.live import Message, Preferences
from services.local_llm import LocalLLM, LocalModelError


@pytest.fixture
def configured(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-a-real-secret")
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")


def test_gemini_endpoint_auth_context_and_extraction(configured, monkeypatch):
    monkeypatch.setenv("LOCAL_LLM_API_KEY", "local-key-must-not-be-sent")
    def respond(request):
        assert str(request.url) == "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key-not-a-real-secret"
        payload = json.loads(request.content)
        assert payload["model"] == "test-gemini-model"
        assert payload["response_format"] == {"type": "json_object"}
        assert 'Rome' in payload["messages"][0]["content"]
        assert payload["messages"][1] == {"role": "user", "content": "I like museums"}
        assert payload["messages"][-1]["content"] == "Go slower"
        assert "test-key" not in request.content.decode()
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps({
            "explanation": "A relaxed pace", "preference_changes": {"pace": "relaxed"}})}}]})
    model = LocalLLM(httpx.Client(transport=httpx.MockTransport(respond)))
    result = model.chat("Go slower", Preferences(destination="Rome"), history=[Message(role="user", content="I like museums")])
    assert result.preference_changes == {"pace": "relaxed"}


@pytest.mark.parametrize("missing", ["GEMINI_API_KEY", "GEMINI_MODEL"])
def test_missing_config_never_calls_provider_or_local_fallback(configured, monkeypatch, missing):
    monkeypatch.delenv(missing)
    def unexpected(request):
        pytest.fail("No HTTP call should happen without explicit Gemini configuration")
    model = LocalLLM(httpx.Client(transport=httpx.MockTransport(unexpected)))
    with pytest.raises(LocalModelError, match=missing):
        model.chat("Hello")


@pytest.mark.parametrize("status,hint", [(401, "GEMINI_API_KEY"), (403, "permissions"), (404, "GEMINI_MODEL"), (429, "quota"), (500, "service")])
def test_provider_errors_are_clear_and_do_not_leak_key(configured, status, hint):
    calls = []
    def respond(request):
        calls.append(str(request.url))
        return httpx.Response(status, json={"error": "test-key-not-a-real-secret"})
    model = LocalLLM(httpx.Client(transport=httpx.MockTransport(respond)))
    with pytest.raises(LocalModelError, match=hint) as error:
        model.chat("Hello")
    assert "test-key" not in str(error.value)
    assert len(calls) == 1  # No silent retry/fallback that could duplicate billable requests.


@pytest.mark.parametrize("content", ["not JSON", '{"explanation":"x","referenced_place_ids":["invented"]}',
    '{"explanation":"x","preference_changes":{"budget":1}}',
    '{"explanation":"x","preference_changes":{"number_of_days":0}}'])
def test_gemini_output_uses_same_grounding_validation(configured, content):
    model = LocalLLM(httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(
        200, json={"choices": [{"message": {"content": content}}]}))))
    with pytest.raises(LocalModelError, match="invalid or ungrounded"):
        model.chat("Hello", Preferences(destination="Rome"))


def test_gemini_connection_error(configured):
    def offline(request):
        raise httpx.ConnectError("offline", request=request)
    with pytest.raises(LocalModelError, match="Cannot connect to Gemini"):
        LocalLLM(httpx.Client(transport=httpx.MockTransport(offline))).chat("Hello")


def test_capabilities_identify_google_without_exposing_credentials(configured):
    # This read-only endpoint needs no service/lifespan (and no production database).
    client = TestClient(app)
    try:
        response = client.get("/capabilities")
        status = response.json()["llm"]
        assert status["provider"] == "gemini" and status["configured"] and status["remote"]
        assert "Google" in status["message"]
        assert "test-key" not in response.text
    finally:
        client.close()


def test_local_default_stays_local_even_if_gemini_key_exists(configured, monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "already-loaded")
    model = LocalLLM()
    assert model.provider == "local" and model.base.startswith("http://localhost:")


def test_invalid_provider_fails_without_fallback(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "invalid")
    with pytest.raises(LocalModelError, match="LLM_PROVIDER"):
        LocalLLM().chat("Hello")


def test_local_provider_still_rejects_non_loopback(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_LLM_BASE_URL", "https://generativelanguage.googleapis.com/v1beta/openai")
    with pytest.raises(LocalModelError, match="loopback"):
        LocalLLM().chat("Hello")
