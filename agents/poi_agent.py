"""Content-based POI recommendation agent."""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from agents.base_agent import BaseAgent
from models.schemas import POI, POIRecommendation, POIRecommendationList, UserTripRequest
from utils.preprocessing import standardise_category
from utils.text_features import TfidfVectorizer, cosine_similarity, tokenize

DEFAULT_WEIGHTS = {
    "preference_similarity": 0.7,
    "rating": 0.2,
    "popularity": 0.1,
}

VALID_WEIGHT_KEYS = {"preference_similarity", "rating", "popularity"}

INTEREST_SYNONYMS: dict[str, list[str]] = {
    "history": ["history", "heritage", "monument", "fort", "ancient"],
    "architecture": ["architecture", "palace", "fort", "tower", "facade", "building"],
    "culture": ["culture", "heritage", "temple", "tradition", "festival"],
    "nature": ["nature", "park", "garden", "beach", "forest", "lake"],
    "food": ["food", "cuisine", "cafe", "restaurant", "market"],
    "shopping": ["shopping", "market", "bazaar", "jewellery"],
    "adventure": ["adventure", "safari", "hiking", "cruise"],
    "nightlife": ["nightlife", "show", "sunset", "evening"],
}


def _minmax(values: list[float]) -> list[float]:
    """Min-max scale values to [0, 1]; all-equal inputs scale to 1.0."""
    if not values:
        return []
    low, high = min(values), max(values)
    if high == low:
        return [1.0] * len(values)
    return [(value - low) / (high - low) for value in values]


def _dedupe_by_id(pois: Sequence[POI]) -> list[POI]:
    """Keep the first occurrence of each poi_id, preserving order."""
    seen: set[str] = set()
    unique: list[POI] = []
    for poi in pois:
        if poi.poi_id not in seen:
            seen.add(poi.poi_id)
            unique.append(poi)
    return unique


class POIRecommendationAgent(BaseAgent):
    """Recommends POIs using TF-IDF cosine similarity against interests.

    Recommendation score is a weighted blend (configurable) of
    preference similarity, rating and review popularity, all normalised
    to [0, 1] before combining.
    """

    name = "poi-recommendation-agent"

    def __init__(
        self,
        pois: Sequence[POI],
        weights: Mapping[str, float] | None = None,
        destination_strict: bool = True,
    ) -> None:
        if not isinstance(pois, Sequence) or isinstance(pois, (str, bytes)):
            raise ValueError("pois must be a sequence of POI records")
        self._pois = list(pois)
        self._weights = self._validate_weights(weights or DEFAULT_WEIGHTS)
        self._destination_strict = destination_strict

    @staticmethod
    def _validate_weights(weights: Mapping[str, float]) -> dict[str, float]:
        if not isinstance(weights, Mapping) or not VALID_WEIGHT_KEYS.issubset(weights):
            raise ValueError(
                f"weights must be a mapping with keys {sorted(VALID_WEIGHT_KEYS)}"
            )
        invalid = {
            key: value
            for key, value in weights.items()
            if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0
        }
        if invalid:
            raise ValueError(f"weights must be non-negative numbers, got {invalid}")
        total = float(sum(weights[key] for key in VALID_WEIGHT_KEYS))
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"weights must sum to 1.0, got {total:.4f}")
        return {key: float(weights[key]) for key in VALID_WEIGHT_KEYS}

    def run(self, input_data: Any) -> POIRecommendationList:
        if not isinstance(input_data, UserTripRequest):
            raise ValueError("input_data must be a UserTripRequest")
        request = input_data

        if not self._pois:
            return POIRecommendationList(request=request, results=[])

        candidates = _dedupe_by_id(self._pois)
        if self._destination_strict and request.destination:
            target = request.destination.strip().lower()
            candidates = [
                poi for poi in candidates if poi.destination.strip().lower() == target
            ]

        if not candidates:
            return POIRecommendationList(request=request, results=[])

        documents = [self._poi_text(poi) for poi in candidates]
        query_text = self._query_text(request)

        vectorizer = TfidfVectorizer().fit([*documents, query_text])
        document_vectors = vectorizer.transform(documents)
        query_vector = vectorizer.transform([query_text])[0]

        rating_norm = _minmax([poi.rating for poi in candidates])
        popularity_norm = _minmax([poi.review_count for poi in candidates])
        matched_by_interest = self._matched_interests(request.interests, candidates)

        results: list[POIRecommendation] = []
        for poi, vector, r_norm, p_norm in zip(
            candidates, document_vectors, rating_norm, popularity_norm
        ):
            preference = cosine_similarity(query_vector, vector)
            score = (
                self._weights["preference_similarity"] * preference
                + self._weights["rating"] * r_norm
                + self._weights["popularity"] * p_norm
            )
            results.append(
                POIRecommendation(
                    poi_id=poi.poi_id,
                    name=poi.name,
                    category=standardise_category(poi.category),
                    recommendation_score=min(1.0, score),
                    rating=poi.rating,
                    visit_duration_hours=poi.visit_duration_hours,
                    estimated_cost=poi.estimated_cost,
                    latitude=poi.latitude,
                    longitude=poi.longitude,
                    reason=self._build_reason(
                        poi, matched_by_interest.get(poi.poi_id, []), r_norm, p_norm
                    ),
                )
            )

        results.sort(key=lambda rec: (-rec.recommendation_score, -rec.rating, rec.poi_id))
        return POIRecommendationList(request=request, results=results)

    @staticmethod
    def _poi_text(poi: POI) -> str:
        description = (poi.description or "").strip()
        if not description:
            description = f"{poi.name} {standardise_category(poi.category)}"
        return (
            f"{standardise_category(poi.category)} "
            f"{poi.destination} {description}"
        )

    @staticmethod
    def _query_text(request: UserTripRequest) -> str:
        interests = " ".join(request.interests)
        if interests.strip():
            expanded = []
            for interest in request.interests:
                synonyms = INTEREST_SYNONYMS.get(interest, [])
                expanded.append(" ".join([interest, *synonyms]))
            return " ".join(expanded)
        return request.destination

    @staticmethod
    def _matched_interests(
        interests: list[str], pois: list[POI]
    ) -> dict[str, list[str]]:
        matched: dict[str, list[str]] = {poi.poi_id: [] for poi in pois}
        for poi in pois:
            poi_tokens = set(tokenize(POIRecommendationAgent._poi_text(poi)))
            for interest in interests:
                tokens = set(tokenize(" ".join([interest, *INTEREST_SYNONYMS.get(interest, [])])))
                if tokens & poi_tokens:
                    matched[poi.poi_id].append(interest)
        return matched

    @staticmethod
    def _build_reason(
        poi: POI,
        matched: list[str],
        rating_norm: float,
        popularity_norm: float,
    ) -> str:
        if matched:
            return "Strong match with selected interests: " + ", ".join(matched)
        if rating_norm >= 0.75:
            return f"Highly rated ({poi.rating:g}/5)"
        if popularity_norm >= 0.75:
            return f"Popular choice ({poi.review_count:,} reviews)"
        return f"General attraction in {poi.destination}"