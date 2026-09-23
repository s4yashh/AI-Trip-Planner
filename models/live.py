"""Validated contracts for persisted, live-data trips. Money is in trip currency."""
from datetime import date, datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


Category = Literal["accommodation", "transportation", "food", "activities", "miscellaneous"]


class Allowances(Model):
    """Total trip allowances, including all travelers, in the trip currency."""
    accommodation: float | None = Field(None, ge=0)
    transportation: float | None = Field(None, ge=0)
    food: float | None = Field(None, ge=0)
    activities: float | None = Field(None, ge=0)
    miscellaneous: float | None = Field(None, ge=0)


class Preferences(Model):
    destination: str = Field(min_length=1, max_length=200)
    number_of_days: int = Field(3, ge=1, le=60)
    start_date: date = Field(default_factory=date.today)
    budget: float | None = Field(None, ge=0)
    currency: Literal["INR", "USD"] = "INR"
    interests: list[str] = Field(default_factory=list, max_length=20)
    travelers: int = Field(1, ge=1, le=20)
    rooms: int = Field(1, ge=1, le=10)
    transport_mode: Literal["walking", "driving"] = "walking"
    dietary_preferences: list[str] = Field(default_factory=list, max_length=10)
    pace: Literal["relaxed", "balanced", "busy"] = "balanced"
    allowances: Allowances = Field(default_factory=Allowances)

    @field_validator("destination")
    @classmethod
    def trim_destination(cls, value):
        if not value.strip():
            raise ValueError("Destination is required")
        return value.strip()


class Source(Model):
    provider: str
    status: Literal["live", "cached", "unavailable", "partial", "estimated"] = "unavailable"
    retrieved_at: str | None = None
    expires_at: str | None = None
    message: str = ""


class Place(Model):
    id: str
    name: str
    kind: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    tags: dict[str, str] = Field(default_factory=dict)
    opening_hours: str | None = None
    phone: str | None = None
    website: str | None = None
    source: Source
    score: float = 0
    reason: str = ""


class HotelOffer(Model):
    id: str
    hotel_id: str
    name: str
    amount: float = Field(ge=0)
    currency: str
    check_in: date
    check_out: date
    rooms: int = Field(ge=1)
    source: Source


class WeatherDay(Model):
    date: date
    temperature_min: float | None = None
    temperature_max: float | None = None
    rain_probability: float | None = None
    wind_kmh: float | None = None
    avoid_outdoor: bool = False


class Route(Model):
    from_id: str
    to_id: str
    minutes: float | None = Field(None, ge=0)
    distance_km: float | None = Field(None, ge=0)
    traffic_delay_minutes: float | None = Field(None, ge=0)
    instructions: list[str] = Field(default_factory=list)
    source: Source


class Activity(Model):
    id: str
    place: Place
    date: date
    start_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    end_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    duration_minutes: int = Field(ge=1)
    duration_basis: str = "Planned visit duration based on your activity pace"
    locked: bool = False
    completed: bool = False
    committed: bool = False


class Expense(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    category: Category
    amount: float = Field(ge=0)
    description: str = Field(min_length=1, max_length=300)
    created_at: str = Field(default_factory=utcnow)


class BudgetLine(Model):
    category: Category
    planned: float | None = None
    spent: float = 0
    projected: float | None = None
    basis: str


class Budget(Model):
    lines: list[BudgetLine] = Field(default_factory=list)
    known_total: float = 0
    total: float | None = None
    spent: float = 0
    complete: bool = False
    within_budget: bool | None = None
    remaining: float | None = None
    conversion_note: str | None = None


class LivePlan(Model):
    places: list[Place] = Field(default_factory=list)
    restaurants: list[Place] = Field(default_factory=list)
    lodging: list[Place] = Field(default_factory=list)
    emergency: list[Place] = Field(default_factory=list)
    hotels: list[HotelOffer] = Field(default_factory=list)
    weather: list[WeatherDay] = Field(default_factory=list)
    routes: list[Route] = Field(default_factory=list)
    activities: list[Activity] = Field(default_factory=list)
    budget: Budget = Field(default_factory=Budget)
    sources: dict[str, Source] = Field(default_factory=dict)
    agents: dict[str, str] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    valid: bool = False
    attempts: int = 0
    timezone: str = "UTC"
    generated_at: str = Field(default_factory=utcnow)


class Message(Model):
    role: Literal["user", "assistant"]
    content: str
    created_at: str = Field(default_factory=utcnow)


class Trip(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    preferences: Preferences
    plan: LivePlan = Field(default_factory=LivePlan)
    expenses: list[Expense] = Field(default_factory=list)
    conversation: list[Message] = Field(default_factory=list)
    monitoring: bool = True
    last_checked: str | None = None
    next_check: str | None = None
    monitoring_error: str | None = None
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)
