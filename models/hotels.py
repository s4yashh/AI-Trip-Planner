"""Contracts for stateless hotel suggestions. Estimated values are always labelled."""
from datetime import date
from typing import Literal

from pydantic import Field, field_validator, model_validator

from models.live import Model, Source


HotelLabel = Literal["Cheapest", "Best rated", "Best value"]
Basis = Literal["openstreetmap", "ai_estimate", "unknown"]


class HotelSearch(Model):
    destination: str = Field(min_length=1, max_length=200)
    check_in: date
    check_out: date
    adults: int = Field(2, ge=1, le=30)
    rooms: int = Field(1, ge=1, le=10)
    currency: Literal["INR", "USD"] = "INR"

    @field_validator("destination")
    @classmethod
    def trim_destination(cls, value):
        if not value.strip():
            raise ValueError("Destination is required")
        return value.strip()

    @model_validator(mode="after")
    def check_dates(self):
        nights = (self.check_out - self.check_in).days
        if nights < 1:
            raise ValueError("Check-out must be at least one day after check-in")
        if nights > 30:
            raise ValueError("Stays longer than 30 nights are not supported")
        return self

    @property
    def nights(self):
        return (self.check_out - self.check_in).days


class HotelSuggestion(Model):
    id: str
    name: str
    area: str | None = None
    distance_km: float | None = Field(None, ge=0)
    latitude: float | None = Field(None, ge=-90, le=90)
    longitude: float | None = Field(None, ge=-180, le=180)
    price_per_night: float | None = Field(None, ge=0)
    price_basis: Basis = "unknown"
    rating: float | None = Field(None, ge=0, le=5)
    rating_basis: Basis = "unknown"
    amenities: list[str] = Field(default_factory=list, max_length=8)
    amenities_basis: Basis = "unknown"
    labels: list[HotelLabel] = Field(default_factory=list)
    website: str | None = None
    verified_listing: bool = True


class HotelSuggestions(Model):
    destination: str
    check_in: date
    check_out: date
    nights: int
    adults: int
    rooms: int
    currency: Literal["INR", "USD"]
    resolved_location: str | None = None
    suggestions: list[HotelSuggestion] = Field(default_factory=list)
    approximate: bool = True
    ai_used: bool = False
    message: str = ""
    sources: dict[str, Source] = Field(default_factory=dict)
