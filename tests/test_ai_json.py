"""Structured AI completion helper; dummy keys and mocked HTTP only."""
import json

import httpx
import pytest

from services.ai_json import complete_json
from services.local_llm import LocalLLM, LocalModelError


@pytest.fixture
def gemini(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-a-real-secret")
    monkeypatch.setenv("GEMINI_MODEL", "test-gemini-model")


def model(handler):
    return LocalLLM(httpx.Client(transport=httpx.MockTransport(handler)))


def test_gemini_json_request_and_fenced_reply(gemini):
    def respond(request):
        payload = json.loads(request.content)
        assert request.headers["authorization"] == "Bearer test-key-not-a-real-secret"
        assert payload["response_format"] == {"type": "json_object"}
        assert payload["messages"] == [{"role": "system", "content": "sys"}, {"role": "user", "content": "hi"}]
        return httpx.Response(200, json={"choices": [{"message": {"content": '```json\n{"hotels": []}\n```'}}]})
    assert complete_json("sys", "hi", llm=model(respond)) == {"hotels": []}


@pytest.mark.parametrize("reply", [httpx.Response(429, text="key=test-key-not-a-real-secret"),
                                   httpx.Response(200, json={"choices": [{"message": {"content": "[1, 2]"}}]}),
                                   httpx.Response(200, json={"choices": []})])
def test_errors_become_model_errors_without_echoing_bodies(gemini, reply):
    with pytest.raises(LocalModelError) as error:
        complete_json("sys", "hi", llm=model(lambda request: reply))
    assert "test-key" not in str(error.value)


def test_unconfigured_local_model_never_calls_out(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "local")
    monkeypatch.setenv("LOCAL_LLM_MODEL", "")
    def fail(request):
        raise AssertionError("must not call the provider")
    with pytest.raises(LocalModelError, match="LOCAL_LLM_MODEL"):
        complete_json("sys", "hi", llm=model(fail))
