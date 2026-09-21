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