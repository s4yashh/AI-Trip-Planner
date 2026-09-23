"""Deterministic day-wise itinerary scheduling agent."""

from __future__ import annotations

import math
from typing import Any, Sequence

from agents.base_agent import BaseAgent
from models.schemas import (
    ItineraryDay,
    ItineraryItem,
    ItineraryRequest,
    ItineraryResponse,
    POIRecommendation,
)


def _to_hhmm(total_minutes: int) -> str:
    total_minutes = max(0, int(total_minutes))
    return f"{total_minutes // 60:02d}:{total_minutes % 60:02d}"


class ItineraryAgent(BaseAgent):
    """Schedules ranked POIs into chronological day-wise itineraries.

    Greedy bin-packing with a configurable daily sightseeing limit:
    higher-ranked POIs are placed first, earlier days are filled
    before later ones, and a visit never starts unless the whole
    visit fits within the remaining daily time.

    The response always contains exactly the requested number of days
    (days with nothing scheduled are returned empty). Optional inputs:

    - ``travel_minutes``: real travel time between consecutive POIs; the
      gap after a visit is ``max(gap_minutes, travel leg)``.
    - ``bad_weather_days``: 1-based day numbers where outdoor POIs are
      avoided unless they fit nowhere else.
    - per-POI ``open_hour``/``close_hour``: a visit is never scheduled
      outside opening hours when these are known.
    """

    name = "itinerary-agent"

    def __init__(
        self,
        daily_hours: float = 8.0,
        day_start_hour: int = 9,
        gap_minutes: int = 15,
    ) -> None:
        if daily_hours <= 0:
            raise ValueError("daily_hours must be positive")
        if not 0 <= day_start_hour <= 23:
            raise ValueError("day_start_hour must be between 0 and 23")
        if gap_minutes < 0:
            raise ValueError("gap_minutes must be zero or positive")
        self._daily_limit_minutes = int(daily_hours * 60)
        self._start_minutes = day_start_hour * 60
        self._gap_minutes = int(gap_minutes)

    def run(self, input_data: Any) -> ItineraryResponse:
        if not isinstance(input_data, ItineraryRequest):
            raise ValueError("input_data must be an ItineraryRequest")
        request = input_data

        pois = self._dedupe(request.ranked_pois)
        requested_days = request.number_of_days
        bad_days = {
            day
            for day in (request.bad_weather_days or [])
            if 1 <= day <= requested_days
        }
        plan = self._bin_pack(pois, requested_days, request.travel_minutes, bad_days)

        days: list[ItineraryDay] = []
        for day_number, placements in enumerate(plan, start=1):
            days.append(
                ItineraryDay(
                    day_number=day_number,
                    items=self._build_items(
                        placements, request.travel_minutes, request.travel_source
                    ),
                )
            )

        planned_ids = {item.poi_id for day in days for item in day.items}
        skipped = [poi.poi_id for poi in pois if poi.poi_id not in planned_ids]
        return ItineraryResponse(
            days=days, skipped_poi_ids=skipped, travel_source=request.travel_source
        )

    @staticmethod
    def _dedupe(pois: Sequence[POIRecommendation]) -> list[POIRecommendation]:
        seen: set[str] = set()
        unique: list[POIRecommendation] = []
        for poi in pois:
            if poi.poi_id not in seen:
                seen.add(poi.poi_id)
                unique.append(poi)
        return unique

    def _placement_gap(
        self, previous: POIRecommendation | None, poi: POIRecommendation,
        travel_minutes: dict[str, float],
    ) -> int:
        """Gap after ``previous`` before ``poi`` starts (travel-aware)."""
        if previous is None:
            return 0
        leg = travel_minutes.get(f"{previous.poi_id}>{poi.poi_id}", 0.0)
        try:
            leg_minutes = max(0, int(math.ceil(float(leg))))
        except (TypeError, ValueError):
            leg_minutes = 0
        return max(self._gap_minutes, leg_minutes)

    def _fits(
        self,
        poi: POIRecommendation,
        cursor: int,
        free: int,
        gap: int,
    ) -> tuple[bool, int, int]:
        """Check a POI fits at ``cursor``; return (fits, start, end)."""
        duration = int(math.ceil(poi.visit_duration_hours * 60))
        start = cursor
        if poi.open_hour is not None:
            start = max(start, int(poi.open_hour) * 60)
        end = start + duration
        day_end = self._start_minutes + self._daily_limit_minutes
        if end > day_end:
            return False, start, end
        if poi.close_hour is not None and end > int(poi.close_hour) * 60:
            return False, start, end
        if free < duration + gap:
            return False, start, end
        return True, start, end

    def _bin_pack(
        self,
        pois: list[POIRecommendation],
        requested_days: int,
        travel_minutes: dict[str, float],
        bad_days: set[int],
    ) -> list[list[tuple[POIRecommendation, int, int]]]:
        plan: list[list[tuple[POIRecommendation, int, int]]] = [
            [] for _ in range(requested_days)
        ]
        free: list[int] = [self._daily_limit_minutes] * requested_days
        cursor: list[int] = [self._start_minutes] * requested_days

        for poi in pois:
            duration = int(math.ceil(poi.visit_duration_hours * 60))
            outdoor = (poi.setting or "outdoor") == "outdoor"
            # Outdoor POIs first try days without bad weather; a second
            # pass allows bad-weather days so ranked POIs are not dropped
            # when they fit nowhere else.
            day_order = list(range(requested_days))
            if outdoor and bad_days:
                day_order = [d for d in day_order if d + 1 not in bad_days] + [
                    d for d in day_order if d + 1 in bad_days
                ]
            for day_index in day_order:
                day = plan[day_index]
                previous = day[-1][0] if day else None
                gap = self._placement_gap(previous, poi, travel_minutes)
                # cursor[day] marks the end of the previous visit; the gap
                # (travel-aware) applies before the next visit starts.
                fits, start, end = self._fits(
                    poi, cursor[day_index] + gap, free[day_index], gap
                )
                if fits:
                    day.append((poi, start, end))
                    free[day_index] -= duration + gap
                    cursor[day_index] = end
                    break
        return plan

    def _build_items(
        self,
        placements: list[tuple[POIRecommendation, int, int]],
        travel_minutes: dict[str, float],
        travel_source: str | None,
    ) -> list[ItineraryItem]:
        items: list[ItineraryItem] = []
        for index, (poi, start, end) in enumerate(placements):
            duration = int(math.ceil(poi.visit_duration_hours * 60))
            travel_to_next: float | None = None
            if index < len(placements) - 1:
                leg = travel_minutes.get(
                    f"{poi.poi_id}>{placements[index + 1][0].poi_id}"
                )
                if leg is not None:
                    try:
                        travel_to_next = round(max(0.0, float(leg)), 1)
                    except (TypeError, ValueError):
                        travel_to_next = None
            items.append(
                ItineraryItem(
                    poi_id=poi.poi_id,
                    name=poi.name,
                    start_time=_to_hhmm(start),
                    end_time=_to_hhmm(end),
                    duration_hours=round(duration / 60, 2),
                    estimated_cost=poi.estimated_cost,
                    travel_minutes_to_next=travel_to_next,
                    travel_source=travel_source if travel_to_next is not None else None,
                )
            )
        return items

    def _schedule_times(self, day_pois: list[POIRecommendation]) -> list[ItineraryItem]:
        cursor = self._start_minutes
        items: list[ItineraryItem] = []
        for poi in day_pois:
            duration = int(math.ceil(poi.visit_duration_hours * 60))
            start = cursor
            end = cursor + duration
            items.append(
                ItineraryItem(
                    poi_id=poi.poi_id,
                    name=poi.name,
                    start_time=_to_hhmm(start),
                    end_time=_to_hhmm(end),
                    duration_hours=round(duration / 60, 2),
                    estimated_cost=poi.estimated_cost,
                )
            )
            cursor = end + self._gap_minutes
        return items