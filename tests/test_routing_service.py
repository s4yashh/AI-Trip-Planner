"""Routing provider behaviour (no network: injected fake fetcher)."""

from __future__ import annotations

from services.routing_service import RoutingService, haversine_km


def test_live_duration_is_used_when_provider_responds():
    service = RoutingService(fetcher=lambda url: {"routes": [{"duration": 900.0}]})
    minutes, source = service.travel_minutes((26.92, 75.82), (26.98, 75.85))
    assert minutes == 15.0
    assert source == "live"


def test_fallback_estimate_is_labelled_when_provider_fails():
    def broken(url):
        raise RuntimeError("no network")

    service = RoutingService(fetcher=broken)
    minutes, source = service.travel_minutes((26.92, 75.82), (26.98, 75.85))
    assert source == "estimate"
    assert minutes > 0


def test_pairwise_reports_live_only_when_all_legs_live():
    service = RoutingService(fetcher=lambda url: {"routes": [{"duration": 600.0}]})
    legs, overall = service.pairwise_minutes(
        [("A", 26.92, 75.82), ("B", 26.98, 75.85)]
    )
    assert set(legs) == {"A>B", "B>A"}
    assert overall == "live"


def test_pairwise_reports_estimate_when_any_leg_falls_back():
    def flaky(url):
        raise RuntimeError("no network")

    service = RoutingService(fetcher=flaky)
    legs, overall = service.pairwise_minutes(
        [("A", 26.92, 75.82), ("B", 26.98, 75.85)]
    )
    assert len(legs) == 2
    assert overall == "estimate"


def test_haversine_distance_is_sane():
    assert haversine_km((26.92, 75.82), (26.92, 75.82)) == 0.0
    assert 5.0 < haversine_km((26.92, 75.82), (26.98, 75.85)) < 15.0


def test_repeated_calls_use_cache():
    calls = []

    def counting(url):
        calls.append(url)
        return {"routes": [{"duration": 600.0}]}

    service = RoutingService(fetcher=counting)
    service.travel_minutes((26.92, 75.82), (26.98, 75.85))
    service.travel_minutes((26.92, 75.82), (26.98, 75.85))
    assert len(calls) == 1
