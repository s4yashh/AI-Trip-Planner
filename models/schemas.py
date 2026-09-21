"""Pydantic schemas for the AI Trip Planner.

These models describe the domain objects exchanged between
the data layer and the future agent layer.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, field_validator

LATITUDE_RANGE = (-90.0, 90.0)
LONGITUDE_RANGE = (-180.0, 180.0)


class POI(BaseModel):
    """A point of interest in the prototype tourism dataset."""

    poi_id: str
    name: str
    destination: str
    category: str
    description: str
    rating: float = Field(ge=0.0, le=5.0)
    review_count: int = Field(ge=0)
    visit_duration_hours: float = Field(ge=0.0)
    estimated_cost: float = Field(ge=0.0)
    latitude: float = Field(ge=LATITUDE_RANGE[0], le=LATITUDE_RANGE[1])
    longitude: float = Field(ge=LONGITUDE_RANGE[0], le=LONGITUDE_RANGE[1])

    @field_validator("description")
    @classmethod
    def description_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("description must not be empty")
        return value.strip()

    @property
    def rank_score(self) -> float:
        """Simple engagement proxy combining rating and review volume."""
        return self.rating * (1 + min(self.review_count, 1_000_000) / 1_000_000)


class UserTripRequest(BaseModel):
    """A user's high-level trip preferences."""

    destination: str
    number_of_days: int = Field(ge=1, le=60)
    budget: Optional[float] = Field(default=None, ge=0.0)
    interests: list[str] = Field(default_factory=list)

    @field_validator("destination")
    @classmethod
    def destination_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("destination must not be empty")
        return value.strip()

    @field_validator("interests")
    @classmethod
    def interests_normalised(cls, value: list[str]) -> list[str]:
        return [interest.strip().lower() for interest in value if interest.strip()]


class POIRecommendation(BaseModel):
    """A single ranked recommendation produced by the POI agent."""

    poi_id: str
    name: str
    category: str
    recommendation_score: float = Field(ge=0.0, le=1.0)
    rating: float = Field(ge=0.0, le=5.0)
    visit_duration_hours: float = Field(ge=0.0)
    estimated_cost: float = Field(ge=0.0)
    reason: str


class POIRecommendationList(BaseModel):
    """Structured recommendation output for a :class:`UserTripRequest`."""

    request: UserTripRequest
    results: list[POIRecommendation] = Field(default_factory=list)


class ItineraryItem(BaseModel):
    """A scheduled visit within one itinerary day."""

    poi_id: str
    name: str
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    duration_hours: float = Field(ge=0.0)
    estimated_cost: float = Field(ge=0.0)


class ItineraryDay(BaseModel):
    """One day of the generated itinerary."""

    day_number: int = Field(ge=1)
    items: list[ItineraryItem] = Field(default_factory=list)


class ItineraryResponse(BaseModel):
    """Day-wise schedule produced by the itinerary agent."""

    days: list[ItineraryDay] = Field(default_factory=list)
    skipped_poi_ids: list[str] = Field(default_factory=list)

    @property
    def days_used(self) -> int:
        return len(self.days)

    @property
    def planned_pois(self) -> list[str]:
        return [item.poi_id for day in self.days for item in day.items]


class ItineraryRequest(BaseModel):
    """Input consumed by the itinerary agent."""

    number_of_days: int = Field(ge=1, le=60)
    ranked_pois: list[POIRecommendation] = Field(default_factory=list)


class BudgetItem(BaseModel):
    """One transparent cost line in the budget breakdown."""

    category: str
    amount: float = Field(ge=0.0)
    basis: str


class BudgetRequest(BaseModel):
    """Input consumed by the budget agent."""

    request: UserTripRequest
    itinerary: ItineraryResponse
    pois: list[POIRecommendation] = Field(default_factory=list)


class BudgetAnalysis(BaseModel):
    """Estimated trip cost compared against the user's budget."""

    accommodation: float = Field(ge=0.0)
    transportation: float = Field(ge=0.0)
    food: float = Field(ge=0.0)
    activities: float = Field(ge=0.0)
    miscellaneous: float = Field(ge=0.0)
    total_cost: float = Field(ge=0.0)
    user_budget: Optional[float] = Field(default=None, ge=0.0)
    within_budget: Optional[bool] = None
    remaining_budget: Optional[float] = None
    suggestions: list[str] = Field(default_factory=list)
    breakdown: list[BudgetItem] = Field(default_factory=list)


class AgentExecutionStatus(BaseModel):
    """Reflects which specialised agents actually completed successfully."""

    poi_recommendation: bool = False
    itinerary: bool = False
    budget: bool = False

    def to_text(self) -> list[str]:
        return [
            self._line("POI Recommendation Agent", self.poi_recommendation),
            self._line("Itinerary Agent", self.itinerary),
            self._line("Budget Agent", self.budget),
        ]

    @staticmethod
    def _line(label: str, ok: bool) -> str:
        mark = "\u2713" if ok else "\u2717"
        return f"{mark} {label}"


class TripPlan(BaseModel):
    """Final structured output of the orchestrator."""

    request: UserTripRequest
    trip_summary: str = ""
    recommended_pois: list[POIRecommendation] = Field(default_factory=list)
    itinerary: ItineraryResponse = Field(default_factory=ItineraryResponse)
    budget_analysis: Optional[BudgetAnalysis] = None
    agent_execution_status: AgentExecutionStatus = Field(default_factory=AgentExecutionStatus)
    errors: list[str] = Field(default_factory=list)