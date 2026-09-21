"""POI recommendation agent behaviour."""

from __future__ import annotations

import pytest

from agents.poi_agent import POIRecommendationAgent
from models.schemas import UserTripRequest


def test_valid_recommendations_return_structured_results(make_poi):
    agent = POIRecommendationAgent(
        [
            make_poi(poi_id="A", name="Art Museum", category="Museum",
                     description="Museum of modern and historic art", rating=4.2),
            make_poi(poi_id="B", name="City Zoo", category="Adventure",
                     description="Zoo with lions tigers and safari animals", rating=3.9),
        ]
    )
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["museum"])
    )
    assert len(result.results) == 2
    for rec in result.results:
        assert rec.poi_id
        assert rec.name
        assert rec.category
        assert rec.recommendation_score >= 0
        assert rec.reason


def test_preference_weight_ranks_matching_poi_first(make_poi):
    agent = POIRecommendationAgent(
        [
            make_poi(poi_id="A", name="Art Museum", category="Museum",
                     description="Museum of modern and historic art"),
            make_poi(poi_id="B", name="City Zoo", category="Adventure",
                     description="Zoo with lions tigers and safari animals"),
        ],
        weights={"preference_similarity": 1.0, "rating": 0.0, "popularity": 0.0},
    )
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["museum"])
    )
    assert result.results[0].poi_id == "A"
    assert result.results[0].recommendation_score > result.results[1].recommendation_score


def test_rating_weight_ranks_highest_rating_first(make_poi):
    agent = POIRecommendationAgent(
        [
            make_poi(poi_id="A", name="Art Museum", category="Museum",
                     description="Museum of modern and historic art", rating=4.2),
            make_poi(poi_id="B", name="City Zoo", category="Adventure",
                     description="Zoo with lions tigers and safari animals", rating=4.9),
        ],
        weights={"preference_similarity": 0.0, "rating": 1.0, "popularity": 0.0},
    )
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["museum"])
    )
    assert result.results[0].poi_id == "B"


def test_popularity_weight_ranks_most_reviewed_first(make_poi):
    agent = POIRecommendationAgent(
        [
            make_poi(poi_id="A", name="Art Museum", category="Museum",
                     description="Museum of modern and historic art", review_count=50),
            make_poi(poi_id="B", name="City Zoo", category="Adventure",
                     description="Zoo with lions tigers and safari animals", review_count=50000),
        ],
        weights={"preference_similarity": 0.0, "rating": 0.0, "popularity": 1.0},
    )
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["museum"])
    )
    assert result.results[0].poi_id == "B"


def test_reason_mentions_matched_interest(make_poi):
    agent = POIRecommendationAgent([make_poi(poi_id="A", description="Historic castle museum")])
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=1, interests=["historic"])
    )
    assert "historic" in result.results[0].reason.lower()


def test_unknown_interests_do_not_crash(make_poi):
    agent = POIRecommendationAgent(
        [make_poi(poi_id="A"), make_poi(poi_id="B", category="Park")]
    )
    result = agent.run(
        UserTripRequest(
            destination="Test City", number_of_days=2, interests=["quantumlevitation"]
        )
    )
    assert len(result.results) == 2
    assert result.results[0].recommendation_score >= 0


def test_missing_description_falls_back(make_poi):
    poi = make_poi(poi_id="A", description="placeholder")
    stripped = poi.model_copy(update={"description": ""})
    agent = POIRecommendationAgent([stripped])
    assert "museum" in agent._poi_text(stripped).lower()
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=1, interests=["museum"])
    )
    assert len(result.results) == 1


def test_empty_dataset_returns_empty(make_poi):
    agent = POIRecommendationAgent([])
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["food"])
    )
    assert result.results == []


def test_destination_without_matching_pois_returns_empty(make_poi):
    agent = POIRecommendationAgent([make_poi(poi_id="A")])
    result = agent.run(
        UserTripRequest(destination="Atlantis", number_of_days=2, interests=["museum"])
    )
    assert result.results == []


def test_destination_filter_is_case_insensitive(make_poi):
    agent = POIRecommendationAgent([make_poi(poi_id="A", destination="Paris")])
    result = agent.run(
        UserTripRequest(destination="paris", number_of_days=2, interests=["museum"])
    )
    assert len(result.results) == 1


def test_duplicate_pois_are_deduplicated(make_poi):
    same = make_poi(poi_id="A")
    agent = POIRecommendationAgent([same, same, same.model_copy()])
    result = agent.run(
        UserTripRequest(destination="Test City", number_of_days=2, interests=["museum"])
    )
    assert len(result.results) == 1


def test_invalid_input_raises(make_poi):
    agent = POIRecommendationAgent([make_poi(poi_id="A")])
    with pytest.raises(ValueError, match="UserTripRequest"):
        agent.run("not a request")


def test_invalid_weights_rejected(make_poi):
    with pytest.raises(ValueError, match="sum to 1.0"):
        POIRecommendationAgent([make_poi()], weights={"preference_similarity": 0.2,
                                                      "rating": 0.2,
                                                      "popularity": 0.2})
    with pytest.raises(ValueError, match="non-negative"):
        POIRecommendationAgent([make_poi()], weights={"preference_similarity": 0.7,
                                                      "rating": -0.1,
                                                      "popularity": 0.4})
    with pytest.raises(ValueError, match="keys"):
        POIRecommendationAgent([make_poi()], weights={"preference_similarity": 1.0,
                                                      "rating": 0.0,
                                                      "unknown": 0.0})


def test_weights_are_configurable_not_hardcoded(make_poi):
    preferred = POIRecommendationAgent([make_poi(poi_id="A")],
                                       weights={"preference_similarity": 0.5,
                                                "rating": 0.3,
                                                "popularity": 0.2})
    assert preferred._weights["preference_similarity"] == 0.5
    assert preferred._weights["rating"] == 0.3
    assert preferred._weights["popularity"] == 0.2