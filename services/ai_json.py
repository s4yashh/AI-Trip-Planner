"""Structured JSON completions through the explicitly configured assistant provider.

Reuses the LocalLLM provider settings (local loopback model or Gemini) without
changing the trip-chat contract. There is no automatic provider fallback.
"""
import json
from urllib.parse import urlparse

import httpx

from services.local_llm import LocalLLM, LocalModelError, llm_status


def ai_configured():
    return llm_status()["configured"]


def ai_label():
    return llm_status()["label"]


def _strip_fences(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1] if "\n" in text else ""
        text = text.rsplit("```", 1)[0]
    return text.strip()


def complete_json(system, user, *, max_tokens=2048, llm=None):
    """Return the provider's JSON object reply, or raise LocalModelError."""
    llm = llm or LocalLLM()
    if llm.provider not in {"local", "gemini"}:
        raise LocalModelError("Set LLM_PROVIDER to local or gemini.")
    if llm.provider == "local":
        parsed = urlparse(llm.base)
        if parsed.hostname not in {"localhost", "127.0.0.1", "::1"} or parsed.scheme not in {"http", "https"}:
            raise LocalModelError("LOCAL_LLM_BASE_URL must address a local loopback server.")
        if not llm.model:
            raise LocalModelError("Set LOCAL_LLM_MODEL to an already loaded model's identifier.")
    elif not llm.api_key or not llm.model:
        raise LocalModelError("Set GEMINI_API_KEY and GEMINI_MODEL in the backend .env and restart the backend.")
    headers = {"Authorization": "Bearer " + llm.api_key} if llm.api_key else {}
    payload = {"model": llm.model, "temperature": 0.2, "max_tokens": max_tokens,
               "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if llm.provider == "gemini":
        payload.update(response_format={"type": "json_object"}, max_tokens=max(max_tokens, 4096))
    try:
        response = llm.client.post(llm.base + "/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        data = json.loads(_strip_fences(response.json()["choices"][0]["message"]["content"]))
        if not isinstance(data, dict):
            raise ValueError("Expected a JSON object")
        return data
    except httpx.HTTPStatusError as exc:
        # Provider response bodies may contain credentials; never echo them.
        raise LocalModelError(f"{llm.label} returned HTTP {exc.response.status_code}.") from exc
    except httpx.RequestError as exc:
        raise LocalModelError(f"Cannot connect to {llm.label}: {type(exc).__name__}") from exc
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise LocalModelError(f"{llm.label} returned invalid structured output.") from exc
