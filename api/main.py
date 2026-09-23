"""FastAPI application exposing the multi-agent trip planner over HTTP.

Run with:  uvicorn api.main:app --reload
The frontend talks to this API through its /api/trip proxy route.
"""

from __future__ import annotations

from datetime import date as _date
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from agents.orchestrator_agent import OrchestratorAgent
from api.presenters import build_trip_response, rate_for
from models.schemas import UserTripRequest

app = FastAPI(
    title="AI Trip Planner API",
    description="Multi-agent trip planning backend (recommendation, itinerary, budget).",
    version="0.3.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_orchestrator: Optional[OrchestratorAgent] = None


class TripApiRequest(BaseModel):
    destination: str
    number_of_days: int = Field(ge=1, le=60)
    budget: Optional[float] = Field(default=None, ge=0.0)
    interests: list[str] = Field(default_factory=list)
    currency: str = Field(default="INR", pattern=r"^(INR|USD)$")
    start_date: Optional[str] = Field(
        default=None,
        description="Trip start date as YYYY-MM-DD; aligns weather forecasts.",
    )

    @field_validator("destination")
    @classmethod
    def destination_not_empty(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("destination is required")
        return value

    @field_validator("interests")
    @classmethod
    def interests_title_case(cls, value: list[str]) -> list[str]:
        return [interest.strip().capitalize() for interest in value if interest.strip()]

    @field_validator("start_date")
    @classmethod
    def start_date_valid(cls, value: str | None) -> str | None:
        if value is None:
            return None
        text = value.strip()
        try:
            _date.fromisoformat(text)
        except ValueError as exc:
            raise ValueError("start_date must be a valid YYYY-MM-DD date") from exc
        return text


def get_orchestrator() -> OrchestratorAgent:
    global _orchestrator
    if _orchestrator is None:
        try:
            _orchestrator = OrchestratorAgent()
        except Exception as exc:  # noqa: BLE001 - surfaced as 503
            raise HTTPException(
                status_code=503,
                detail=f"AI backend unavailable (dataset could not be loaded): {exc}",
            ) from exc
    return _orchestrator


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/trip")
def create_trip(payload: TripApiRequest) -> dict:
    try:
        usd_budget = (
            payload.budget
            if payload.budget is None
            else payload.budget / rate_for(payload.currency)
        )
        request = UserTripRequest(
            destination=payload.destination,
            number_of_days=payload.number_of_days,
            budget=usd_budget,
            interests=payload.interests,
            start_date=payload.start_date,
        )
        plan = get_orchestrator().run(request)
        return build_trip_response(plan, payload.currency)
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001 - no raw stack traces in the UI
        raise HTTPException(
            status_code=500, detail=f"trip planning failed: {exc}"
        ) from exc