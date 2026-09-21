"""API integration tests: HTTP boundary -> orchestrator -> real agents."""

from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_trip_jaipur_full_flow():
    payload = {
        "destination": "Jaipur",
        "number_of_days": 3,
        "budget": 30000,
        "interests": ["History", "Architecture", "Culture"],
        "currency": "INR",
    }
    response = client.post("/trip", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["trip_summary"]["destination"] == "Jaipur"
    assert data["trip_summary"]["number_of_days"] == 3
    assert data["recommended_pois"]
    assert data["itinerary"]["days"]
    assert data["budget_analysis"] is not None
    assert data["agent_execution_status"]["poi_recommendation"] is True
    assert data["agent_execution_status"]["itinerary"] is True
    assert data["agent_execution_status"]["budget"] is True
    assert data["errors"] == []

    first = data["recommended_pois"][0]
    for field in ("poi_id", "name", "category", "recommendation_score",
                  "rating", "visit_duration_hours", "estimated_cost", "reason"):
        assert field in first

    budget = data["budget_analysis"]
    assert budget["total_cost"] > 0
    assert sum(
        budget[category] for category in
        ("accommodation", "transportation", "food", "activities", "miscellaneous")
    ) == budget["total_cost"]


def test_trip_paris_different_preferences():
    response = client.post(
        "/trip",
        json={
            "destination": "Paris",
            "number_of_days": 2,
            "budget": 500,
            "interests": ["Food"],
            "currency": "USD",
        },
    )
    assert response.status_code == 200
    data = response.json()
    names = {rec["name"] for rec in data["recommended_pois"]}
    assert "Le Marais Walking Tour" in names
    assert all(
        rec["category"] in {"museum", "food", "landmark", "entertainment", "adventure"}
        for rec in data["recommended_pois"]
    )


def test_trip_budget_exceeded_returns_suggestions():
    response = client.post(
        "/trip",
        json={
            "destination": "Jaipur",
            "number_of_days": 3,
            "budget": 100,
            "interests": ["History"],
            "currency": "INR",
        },
    )
    assert response.status_code == 200
    budget = response.json()["budget_analysis"]
    assert budget["within_budget"] is False
    assert budget["remaining_budget"] < 0
    assert budget["suggestions"]


def test_trip_no_matching_destination_is_graceful():
    response = client.post(
        "/trip",
        json={"destination": "Atlantis", "number_of_days": 2, "interests": ["Food"]},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["recommended_pois"] == []
    assert data["itinerary"]["days"] == []
    assert data["budget_analysis"] is None
    assert data["errors"]
    assert data["agent_execution_status"]["poi_recommendation"] is True
    assert data["agent_execution_status"]["itinerary"] is False


def test_trip_missing_destination_is_rejected():
    response = client.post("/trip", json={"number_of_days": 2, "interests": ["Food"]})
    assert response.status_code == 422


def test_trip_invalid_days_is_rejected():
    response = client.post(
        "/trip", json={"destination": "Rome", "number_of_days": 0, "interests": ["Food"]}
    )
    assert response.status_code == 422


def test_trip_negative_budget_is_rejected():
    response = client.post(
        "/trip",
        json={"destination": "Rome", "number_of_days": 2, "budget": -5, "interests": []},
    )
    assert response.status_code == 422


def test_trip_invalid_currency_is_rejected():
    response = client.post(
        "/trip",
        json={"destination": "Rome", "number_of_days": 2, "currency": "EUR"},
    )
    assert response.status_code == 422