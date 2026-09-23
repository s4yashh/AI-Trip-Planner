"""Isolated browser acceptance harness. Only run explicitly with -m tests.browser_server.

Uses a temporary database and fixture providers. The normal application never imports this.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import uvicorn

from api.main import app
from agents.live_orchestrator import LiveOrchestrator
from models.live import Message
from services.local_llm import ChatResult
from services.trip_service import TripService
from services.trip_store import TripStore
from tests.test_live_planning import FixtureProviders


class FixtureLocalModel:
    def chat(self, message, *args):
        return ChatResult(explanation="The test model extracted a relaxed pace.", preference_changes={"pace": "relaxed"})


if __name__ == "__main__":
    with TemporaryDirectory(prefix="trip-browser-test-") as directory:
        provider = FixtureProviders()
        clock = [datetime.now(timezone.utc)]
        service = TripService(TripStore(Path(directory) / "browser.sqlite3"), LiveOrchestrator(provider),
                              llm=FixtureLocalModel(), clock=lambda: clock[0])
        app.state.service = service

        @app.post("/__test__/weather-change")
        def weather_change():
            provider.rain = True
            clock[0] += timedelta(minutes=16)
            service.monitor_once()
            return {"ok": True}

        uvicorn.run(app, host="127.0.0.1", port=8001)
