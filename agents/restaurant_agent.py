"""Restaurant agent: ranks real restaurant listings with our own algorithm.

The external places provider supplies raw listings; all intelligence
(cuisine match, rating, budget fit, distance) lives in this agent under a
transparent, configurable weighted formula::

    restaurant_score = 0.40 * cuisine_similarity
                     + 0.25 * rating_score
                     + 0.20 * budget_fit
                     + 0.15 * distance_score

When the live provider is unreachable, the agent falls back to the local
restaurant dataset (labelled ``dataset``) or returns a clear unavailable
state. It never fabricates restaurant information.
"""

from __future__ import annotations

from typing import Any, Mapping

from agents.base_agent import BaseAgent
from models.schemas import (
    Restaurant,
    RestaurantList,
    RestaurantRequest,
    UserTripRequest,
)
from services.places_service import (
    DEFAULT_RESTAURANT_DATASET,
    OverpassPlacesService,
    PlacesServiceError,
    load_local_restaurants,
)
from services.routing_service import haversine_km
from utils.text_features import TfidfVectorizer, cosine_similarity

DEFAULT_RESTAURANT_WEIGHTS = {
    "cuisine_similarity": 0.40,
    "rating": 0.25,
    "budget_fit": 0.20,
    "distance": 0.15,
}

VALID_RESTAURANT_WEIGHT_KEYS = set(DEFAULT_RESTAURANT_WEIGHTS)

INTEREST_TO_CUISINE: dict[str, list[str]] = {
    "food": ["indian", "italian", "japanese", "french", "chinese", "cafe"],
    "culture": ["traditional", "local"],
    "history": ["traditional", "heritage"],
    "nightlife": ["bar", "contemporary"],
    "shopping": ["cafe"],
    "nature": ["organic", "healthy"],
    "adventure": ["street food"],
    "architecture": ["heritage"],
}


def affordable_price_level(daily_food_budget: float | None) -> int:
    """Map a daily food budget (USD) to an affordable price level 1-3."""
    if daily_food_budget is None:
        return 3
    if daily_food_budget < 12.0:
        return 1
    if daily_food_budget < 30.0:
        return 2
    return 3


class RestaurantAgent(BaseAgent):
    """Ranks restaurant candidates for a trip request."""

    name = "restaurant-agent"

    def __init__(
        self,
        service: OverpassPlacesService | None = None,
        weights: Mapping[str, float] | None = None,
        dataset_path: str | None = None,
        top_k: int = 5,
    ) -> None:
        self._service = service or OverpassPlacesService()
        self._weights = self._validate_weights(weights or DEFAULT_RESTAURANT_WEIGHTS)
        self._dataset_path = dataset_path  # Explicit fixtures/imports only; no runtime sample fallback.
        if top_k < 1:
            raise ValueError("top_k must be at least 1")
        self._top_k = top_k

    @staticmethod
    def _validate_weights(weights: Mapping[str, float]) -> dict[str, float]:
        if (
            not isinstance(weights, Mapping)
            or set(weights) != VALID_RESTAURANT_WEIGHT_KEYS
        ):
            raise ValueError(
                "weights must be a mapping with keys "
                f"{sorted(VALID_RESTAURANT_WEIGHT_KEYS)}"
            )
        invalid = {
            key: value
            for key, value in weights.items()
            if isinstance(value, bool)
            or not isinstance(value, (int, float))
            or value < 0
        }
        if invalid:
            raise ValueError(f"weights must be non-negative numbers, got {invalid}")
        total = float(sum(weights.values()))
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total:.4f}")
        return {key: float(value) for key, value in weights.items()}

    def run(self, input_data: Any) -> RestaurantList:
        if not isinstance(input_data, RestaurantRequest):
            raise ValueError("input_data must be a RestaurantRequest")
        request = input_data.request

        candidates, source = self._load_candidates(request, input_data)
        if not candidates:
            return RestaurantList(
                request=request,
                results=[],
                source="unavailable",
                message="Live restaurant data unavailable and no local "
                "fallback exists for this destination.",
            )

        ranked = self._rank(
            candidates,
            request,
            input_data.latitude,
            input_data.longitude,
            input_data.daily_food_budget,
        )
        return RestaurantList(
            request=request,
            results=ranked[: self._top_k],
            source=source,
            message=(
                "Ranked live restaurant listings."
                if source == "live"
                else "Ranked local dataset restaurants (live data unavailable)."
            ),
        )

    def _load_candidates(
        self, request: UserTripRequest, payload: RestaurantRequest
    ) -> tuple[list[dict[str, Any]], str]:
        if payload.latitude is not None and payload.longitude is not None:
            try:
                listings = self._service.nearby_restaurants(
                    payload.latitude, payload.longitude
                )
                if listings:
                    return listings, "live"
            except PlacesServiceError:
                pass
        fallback = load_local_restaurants(self._dataset_path, request.destination) if self._dataset_path else []
        if fallback:
            return fallback, "dataset"
        return [], "unavailable"

    def _rank(
        self,
        candidates: list[dict[str, Any]],
        request: UserTripRequest,
        latitude: float | None,
        longitude: float | None,
        daily_food_budget: float | None,
    ) -> list[Restaurant]:
        query = self._query_text(request.interests)
        documents = [
            f"{candidate.get('cuisine', '')} {candidate.get('name', '')}"
            for candidate in candidates
        ]
        vectorizer = TfidfVectorizer().fit([*documents, query])
        query_vector = vectorizer.transform([query])[0]
        document_vectors = vectorizer.transform(documents)

        scored: list[Restaurant] = []
        for candidate, vector in zip(candidates, document_vectors):
            cuisine = cosine_similarity(query_vector, vector)
            rating = self._rating_score(candidate)
            budget = self._budget_fit(candidate, daily_food_budget)
            distance_km, distance = self._distance_score(
                candidate, latitude, longitude
            )
            score = (
                self._weights["cuisine_similarity"] * cuisine
                + self._weights["rating"] * rating
                + self._weights["budget_fit"] * budget
                + self._weights["distance"] * distance
            )
            scored.append(
                Restaurant(
                    restaurant_id=str(candidate.get("restaurant_id") or candidate.get("name")),
                    name=str(candidate.get("name") or "Unnamed restaurant"),
                    cuisine=str(candidate.get("cuisine") or ""),
                    rating=float(candidate.get("rating") or 0.0),
                    price_level=int(candidate.get("price_level") or 2),
                    latitude=candidate.get("latitude"),
                    longitude=candidate.get("longitude"),
                    distance_km=distance_km,
                    restaurant_score=min(1.0, max(0.0, score)),
                    reason=self._build_reason(candidate, cuisine, budget),
                    source=str(candidate.get("source") or "dataset"),
                )
            )
        scored.sort(key=lambda item: (-item.restaurant_score, -item.rating))
        return scored

    @staticmethod
    def _query_text(interests: list[str]) -> str:
        expanded: list[str] = []
        for interest in interests:
            expanded.append(interest)
            expanded.extend(INTEREST_TO_CUISINE.get(interest, []))
        return " ".join(expanded) if expanded else "restaurant food dining"

    @staticmethod
    def _rating_score(candidate: dict[str, Any]) -> float:
        try:
            return max(0.0, min(1.0, float(candidate.get("rating") or 0.0) / 5.0))
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _budget_fit(
        candidate: dict[str, Any], daily_food_budget: float | None
    ) -> float:
        if daily_food_budget is None:
            return 1.0
        try:
            price = int(candidate.get("price_level") or 2)
        except (TypeError, ValueError):
            price = 2
        affordable = affordable_price_level(daily_food_budget)
        if price <= affordable:
            return 1.0
        return max(0.0, 1.0 - 0.4 * (price - affordable))

    @staticmethod
    def _distance_score(
        candidate: dict[str, Any], latitude: float | None, longitude: float | None
    ) -> tuple[float | None, float]:
        lat, lon = candidate.get("latitude"), candidate.get("longitude")
        if latitude is None or longitude is None or lat is None or lon is None:
            return None, 0.5
        try:
            distance = haversine_km((latitude, longitude), (float(lat), float(lon)))
        except (TypeError, ValueError):
            return None, 0.5
        return round(distance, 2), 1.0 / (1.0 + distance / 5.0)

    @staticmethod
    def _build_reason(
        candidate: dict[str, Any], cuisine: float, budget: float
    ) -> str:
        parts: list[str] = []
        if cuisine >= 0.3 and candidate.get("cuisine"):
            parts.append(f"matches your taste ({candidate['cuisine']})")
        try:
            rating = float(candidate.get("rating") or 0.0)
        except (TypeError, ValueError):
            rating = 0.0
        if rating >= 4.5:
            parts.append(f"highly rated ({rating:g}/5)")
        if budget >= 1.0:
            parts.append("fits the food budget")
        if not parts:
            source = candidate.get("source")
            if source == "live":
                return "Live listing near your destination (no rating published)."
            return "Local restaurant option for this destination."
        return "Good pick: " + "; ".join(parts) + "."
