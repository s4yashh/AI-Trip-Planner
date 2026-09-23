"""Trip lifecycle: user changes and background refresh share one validated path."""
import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from agents.live_orchestrator import LiveOrchestrator
from models.live import Message, Preferences, Trip, utcnow
from services.local_llm import LocalLLM
from services.trip_store import ConflictError, TripStore

logger = logging.getLogger(__name__)


class TripService:
    def __init__(self, store=None, planner=None, llm=None, clock=None):
        self.store = store or TripStore()
        self.planner = planner or LiveOrchestrator()
        self.llm = llm or LocalLLM()
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.interval = max(60, int(os.getenv("MONITOR_INTERVAL_SECONDS", "900")))
        self.monitor_lock = threading.Lock()

    def next_check(self):
        return (self.clock() + timedelta(seconds=self.interval)).isoformat()

    def create(self, preferences):
        prefs = Preferences.model_validate(preferences)
        plan = self.planner.run(prefs, now=self.clock())
        trip = Trip(preferences=prefs, plan=plan, last_checked=self.clock().isoformat(), next_check=self.next_check())
        return self.store.create(trip)

    def checked(self, trip_id, version):
        trip = self.store.get(trip_id)
        if trip.version != version:
            raise ConflictError("Trip changed. Reload the latest version before editing.")
        return trip

    def replan(self, trip, reason):
        candidate = self.planner.run(trip.preferences, previous=trip.plan, expenses=trip.expenses, now=self.clock())
        old = trip.plan
        if candidate.valid:
            trip.plan = candidate
            trip.monitoring_error = None
        else:
            # Keep times and identities; publish fresh budget/provider state and unresolved conflicts.
            candidate.activities = old.activities
            candidate.routes = old.routes
            candidate.timezone = old.timezone
            candidate.warnings = list(dict.fromkeys(candidate.warnings + ["Previous itinerary retained because a valid revision was not found."]))
            trip.plan = candidate
            trip.monitoring_error = "; ".join(candidate.conflicts)
        trip.last_checked = self.clock().isoformat()
        trip.next_check = self.next_check() if trip.monitoring else None
        changes = self.describe_changes(old, trip.plan)
        return self.store.save(trip, trip.version, reason + (": " + "; ".join(changes) if changes else ": conditions checked"),
                               revision=bool(changes) or reason != "Automatic refresh")

    @staticmethod
    def describe_changes(before, after):
        changes = []
        old = {a.id: a for a in before.activities}
        new = {a.id: a for a in after.activities}
        for key in old.keys()-new.keys():
            changes.append(f"Removed {old[key].place.name}")
        for key in new.keys()-old.keys():
            changes.append(f"Added {new[key].place.name}")
        for key in old.keys() & new.keys():
            if (old[key].date, old[key].start_time) != (new[key].date, new[key].start_time):
                changes.append(f"Rescheduled {new[key].place.name}")
        if before.budget != after.budget:
            changes.append("Budget recalculated")
        if before.conflicts != after.conflicts:
            changes.append("Planning conflicts updated")
        if before.weather != after.weather:
            changes.append("Weather forecast updated")
        if [(r.from_id, r.to_id, r.minutes, r.traffic_delay_minutes) for r in before.routes] != [
                (r.from_id, r.to_id, r.minutes, r.traffic_delay_minutes) for r in after.routes]:
            changes.append("Route or traffic times updated")
        old_hotels = {(h.hotel_id, h.amount, h.currency) for h in before.hotels}
        new_hotels = {(h.hotel_id, h.amount, h.currency) for h in after.hotels}
        if old_hotels != new_hotels:
            changes.append("Hotel offers changed")
        return changes

    def update(self, trip_id, version, preferences=None, monitoring=None):
        trip = self.checked(trip_id, version)
        if monitoring is not None:
            trip.monitoring = monitoring
            trip.next_check = self.next_check() if monitoring else None
        if preferences is not None:
            self.validate_preference_change(trip, preferences)
            trip.preferences = preferences
            return self.replan(trip, "Preferences updated")
        return self.store.save(trip, version, "Monitoring enabled" if trip.monitoring else "Monitoring paused")

    def validate_preference_change(self, trip, preferences):
        if trip.expenses and preferences.currency != trip.preferences.currency:
            raise ConflictError("Currency cannot change after expenses are recorded. Create a separate trip for another currency.")
        protected = [a for a in trip.plan.activities if a.locked or a.completed or a.committed or
                     datetime.fromisoformat(f"{a.date}T{a.start_time}").replace(tzinfo=ZoneInfo(trip.plan.timezone)) <= self.clock()]
        if protected and preferences.destination.casefold() != trip.preferences.destination.casefold():
            raise ConflictError("This trip has protected activities. Create a new trip to change destination.")
        end = preferences.start_date + timedelta(days=preferences.number_of_days-1)
        if any(not preferences.start_date <= a.date <= end for a in protected):
            raise ConflictError("New dates exclude protected activities. Keep their dates or adjust those commitments first.")

    def activity(self, trip_id, activity_id, version, changes):
        trip = self.checked(trip_id, version)
        activity = next((a for a in trip.plan.activities if a.id == activity_id), None)
        if activity is None:
            raise KeyError(activity_id)
        for key, value in changes.items():
            setattr(activity, key, value)
        return self.replan(trip, f"Updated activity: {activity.place.name}")

    def expense(self, trip_id, version, expense):
        trip = self.checked(trip_id, version)
        trip.expenses.append(expense)
        return self.replan(trip, f"Expense recorded: {expense.category}")

    def chat(self, trip_id, version, message):
        trip = self.checked(trip_id, version)
        result = self.llm.chat(message, trip.preferences, trip.plan, trip.conversation)
        trip.conversation.extend([Message(role="user", content=message), Message(role="assistant", content=result.explanation)])
        if result.preference_changes:
            data = trip.preferences.model_dump(mode="json")
            data.update(result.preference_changes)
            updated = Preferences.model_validate(data)
            self.validate_preference_change(trip, updated)
            trip.preferences = updated
            return self.replan(trip, "Preferences updated through local conversation")
        return self.store.save(trip, version, "Conversation updated", revision=False)

    def monitor_once(self):
        if not self.monitor_lock.acquire(blocking=False):
            return
        try:
            for trip in self.store.list():
                now = self.clock()
                end = trip.preferences.start_date + timedelta(days=trip.preferences.number_of_days)
                local_now = now.astimezone(ZoneInfo(trip.plan.timezone))
                if not trip.monitoring or local_now.date() >= end:
                    continue
                # Monitor trips in the weather forecast window, including ongoing trips.
                if trip.preferences.start_date > local_now.date() + timedelta(days=15):
                    continue
                if trip.next_check and datetime.fromisoformat(trip.next_check) > now:
                    continue
                try:
                    self.replan(trip, "Automatic refresh")
                except ConflictError:
                    continue  # A user's newer version always wins.
                except Exception:
                    logger.exception("Background trip refresh failed for %s", trip.id)
                    trip.monitoring_error = "Background refresh failed; the previous itinerary is retained. Retry manually."
                    trip.next_check = self.next_check()
                    try:
                        self.store.save(trip, trip.version, "Refresh failed", revision=False)
                    except ConflictError:
                        pass
        finally:
            self.monitor_lock.release()
