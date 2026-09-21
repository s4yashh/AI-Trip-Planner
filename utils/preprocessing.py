"""Cleaning helpers applied after the raw dataset is loaded."""

from __future__ import annotations

from typing import Callable, Optional

from models.schemas import POI


def standardise_category(value: str) -> str:
    """Normalise a category to a canonical, lower-case token."""
    return " ".join(value.strip().lower().split())


def is_missing(value: Optional[object]) -> bool:
    """True when a value is None, an empty string, or 'nan'."""
    if value is None:
        return True
    if isinstance(value, str) and not value.strip():
        return True
    if isinstance(value, str) and value.strip().lower() == "nan":
        return True
    return False


def filter_pois(pois: list[POI], predicate: Callable[[POI], bool]) -> list[POI]:
    """Return POIs matching a predicate, preserving dataset order."""
    return [poi for poi in pois if predicate(poi)]


def with_field(pois: list[POI], field: str) -> list[POI]:
    """Keep POIs whose field is present and non-empty."""
    missing = ["", None, "nan"]
    return [poi for poi in pois if getattr(poi, field, None) not in missing]


def fill_missing(pois: list[POI], field: str, default: object) -> list[POI]:
    """Replace missing values in a field with a supplied default."""
    for poi in pois:
        if getattr(poi, field) in (None, "", "nan"):
            setattr(poi, field, default)
    return pois