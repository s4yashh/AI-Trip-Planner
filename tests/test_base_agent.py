"""Base agent contract behaviour."""

from __future__ import annotations

import pytest

from agents.base_agent import BaseAgent


class DummyAgent(BaseAgent):
    name = "dummy"

    def run(self, input_data):
        return {"received": input_data}


def test_base_agent_cannot_be_instantiated():
    with pytest.raises(TypeError):
        BaseAgent()  # type: ignore[abstract]


def test_concrete_agent_runs():
    agent = DummyAgent()
    assert agent.run("hello") == {"received": "hello"}


def test_agent_special_str():
    assert "DummyAgent" in repr(DummyAgent())