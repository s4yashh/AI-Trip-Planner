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
        plan = self._bin_pack(pois, requested_days)

        days: list[ItineraryDay] = []
        for day_number, day_pois in enumerate(plan, start=1):
            if not day_pois:
                continue
            days.append(
                ItineraryDay(
                    day_number=day_number,
                    items=self._schedule_times(day_pois),
                )
            )

        planned_ids = {item.poi_id for day in days for item in day.items}
        skipped = [poi.poi_id for poi in pois if poi.poi_id not in planned_ids]
        return ItineraryResponse(days=days, skipped_poi_ids=skipped)

    @staticmethod
    def _dedupe(pois: Sequence[POIRecommendation]) -> list[POIRecommendation]:
        seen: set[str] = set()
        unique: list[POIRecommendation] = []
        for poi in pois:
            if poi.poi_id not in seen:
                seen.add(poi.poi_id)
                unique.append(poi)
        return unique

    def _bin_pack(
        self, pois: list[POIRecommendation], requested_days: int
    ) -> list[list[POIRecommendation]]:
        plan: list[list[POIRecommendation]] = [[] for _ in range(requested_days)]
        free: list[int] = [self._daily_limit_minutes] * requested_days

        for poi in pois:
            duration = int(math.ceil(poi.visit_duration_hours * 60))
            for day_index, day in enumerate(plan):
                need = duration + (self._gap_minutes if day else 0)
                if free[day_index] >= need:
                    day.append(poi)
                    free[day_index] -= need
                    break
        return plan

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