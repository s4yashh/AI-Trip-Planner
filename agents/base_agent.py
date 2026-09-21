"""Abstract contract every AI agent must implement."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """Abstract base class for all trip-planning agents.

    Subclasses implement :meth:`run`, which accepts a validated input
    payload (typically a Pydantic model) and returns a structured
    result. The generic ``TIn`` / ``TOut`` type parameters are expanded
    as concrete agents are added.
    """

    name: str = "base-agent"

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """Execute the agent's core logic against ``input_data``.

        Must be implemented by every concrete agent. The concrete
        input and return types are determined by each subclass.
        """
        raise NotImplementedError

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return f"<{type(self).__name__} name={self.name!r}>"