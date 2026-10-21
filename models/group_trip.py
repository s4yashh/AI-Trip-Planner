"""Contracts for additive, group-only trip planning."""
from datetime import date
from typing import Literal
from uuid import uuid4

from pydantic import Field, field_validator

from models.live import LivePlan, Model, utcnow


GroupPace = Literal["relaxed", "moderate", "packed"]
BudgetStatus = Literal["within", "over", "unknown"]


class GroupTripCreate(Model):
    destination: str = Field(min_length=1, max_length=200)
    start_date: date = Field(default_factory=date.today)
    number_of_days: int = Field(default=3, ge=1, le=30)
    member_count: int = Field(ge=2, le=20)
    currency: Literal["INR", "USD"] = "INR"

    @field_validator("destination")
    @classmethod
    def trim_destination(cls, value):
        if not value.strip():
            raise ValueError("Destination is required")
        return value.strip()


class GroupMemberPreferences(Model):
    budget: float | None = Field(default=None, ge=0)
    interests: list[str] = Field(min_length=1, max_length=20)
    pace: GroupPace = "moderate"

    @field_validator("interests")
    @classmethod
    def clean_interests(cls, values):
        cleaned = list(dict.fromkeys(value.strip() for value in values if value.strip()))
        if not cleaned:
            raise ValueError("Enter at least one interest")
        return cleaned


class GroupMember(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = Field(min_length=1, max_length=80)
    preferences: GroupMemberPreferences | None = None


class GroupTripVersion(Model):
    version: int = Field(ge=1)


class GroupMemberUpdate(GroupTripVersion):
    preferences: GroupMemberPreferences


class MemberCoverage(Model):
    member_id: str
    member_name: str
    top_interests: list[str] = Field(default_factory=list)
    covered_interests: list[str] = Field(default_factory=list)


class GroupConflict(Model):
    conflict_type: Literal["interests", "pace", "budget"]
    members: list[str] = Field(default_factory=list)
    description: str
    resolution: str
    resolved: bool


class MemberBudgetCheck(Model):
    member_id: str
    member_name: str
    budget: float | None
    known_share: float
    status: BudgetStatus
    note: str


class GroupBudget(Model):
    currency: Literal["INR", "USD"]
    total_estimate: float | None = None
    known_total: float = Field(ge=0)
    estimated_per_member: float | None = None
    known_per_member: float = Field(ge=0)
    estimate_complete: bool = False
    member_checks: list[MemberBudgetCheck] = Field(default_factory=list)


class GroupPlan(Model):
    itinerary: LivePlan
    why_this_plan: str
    member_coverage: list[MemberCoverage] = Field(default_factory=list)
    conflicts: list[GroupConflict] = Field(default_factory=list)
    budget: GroupBudget


class GroupTrip(Model):
    id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = Field(default=1, ge=1)
    destination: str
    start_date: date
    number_of_days: int
    member_count: int
    currency: Literal["INR", "USD"]
    members: list[GroupMember]
    plan: GroupPlan | None = None
    created_at: str = Field(default_factory=utcnow)
    updated_at: str = Field(default_factory=utcnow)
