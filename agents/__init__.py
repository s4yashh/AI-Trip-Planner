"""Agent definitions for the AI Trip Planner.

This stage ships the abstract contract plus four concrete agents:

* :class:`POIRecommendationAgent` - content-based POI ranking
* :class:`ItineraryAgent` - deterministic day-wise scheduling
* :class:`BudgetAgent` - transparent trip cost estimation
* :class:`OrchestratorAgent` - coordinates the specialised agents

Future agents (LLM, real-time APIs, ...) are intentionally not defined.
"""

from agents.base_agent import BaseAgent
from agents.budget_agent import BudgetAgent
from agents.itinerary_agent import ItineraryAgent
from agents.orchestrator_agent import OrchestratorAgent
from agents.poi_agent import POIRecommendationAgent

__all__ = [
    "BaseAgent",
    "POIRecommendationAgent",
    "ItineraryAgent",
    "BudgetAgent",
    "OrchestratorAgent",
]