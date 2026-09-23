"""Local application HTTP boundary and resumable monitoring lifecycle."""
from contextlib import asynccontextmanager
import asyncio
import logging
import os
from pathlib import Path

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import Field

from api.compatibility import legacy_response
from models.live import Expense, Model, Preferences
from services.local_llm import LocalModelError
from services.trip_service import TripService
from services.trip_store import ConflictError

logger = logging.getLogger(__name__)


def get_service():
    if not hasattr(app.state, "service"):
        app.state.service = TripService()
    return app.state.service


@asynccontextmanager
async def lifespan(application):
    service = get_service()
    stop = asyncio.Event()
    async def monitor():
        while not stop.is_set():
            try:
                await asyncio.to_thread(service.monitor_once)
            except Exception:
                logger.exception("Monitor cycle failed")
            try:
                await asyncio.wait_for(stop.wait(), timeout=30)
            except asyncio.TimeoutError:
                pass
    task = asyncio.create_task(monitor())
    yield
    stop.set()
    await task


app = FastAPI(title="Adaptive AI Trip Planner", version="1.0.0", lifespan=lifespan)
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH"], allow_headers=["Content-Type"])


@app.middleware("http")
async def local_origin(request: Request, call_next):
    origin = request.headers.get("origin")
    if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin not in origins:
        return JSONResponse(status_code=403, content={"detail": "This local app only accepts requests from its own UI."})
    return await call_next(request)


@app.exception_handler(ConflictError)
async def conflict(request, exc):
    return JSONResponse(status_code=409, content={"detail": str(exc)})


@app.exception_handler(KeyError)
async def missing(request, exc):
    return JSONResponse(status_code=404, content={"detail": "Trip or activity not found."})


@app.exception_handler(LocalModelError)
async def model_error(request, exc):
    return JSONResponse(status_code=503, content={"detail": str(exc)})


class Versioned(Model):
    version: int = Field(ge=1)


class TripUpdate(Versioned):
    preferences: Preferences | None = None
    monitoring: bool | None = None


class ActivityUpdate(Versioned):
    locked: bool | None = None
    completed: bool | None = None
    committed: bool | None = None


class ExpenseInput(Versioned):
    expense: Expense


class ChatInput(Versioned):
    message: str = Field(min_length=1, max_length=4000)


class DraftChat(Model):
    message: str = Field(min_length=1, max_length=4000)
    preferences: Preferences | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/capabilities")
def capabilities():
    return {"local_model": {"configured": bool(os.getenv("LOCAL_LLM_MODEL")),
                            "message": "Local model configured; availability is checked when you send a message." if os.getenv("LOCAL_LLM_MODEL")
                            else "Set LOCAL_LLM_MODEL to use an already running local model. The trip form works without it."},
            "hotels_configured": bool(os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET")),
            "traffic_configured": bool(os.getenv("TOMTOM_API_KEY"))}


@app.get("/trips")
def list_trips():
    return [{"id": t.id, "version": t.version, "destination": t.preferences.destination,
             "start_date": t.preferences.start_date, "number_of_days": t.preferences.number_of_days,
             "monitoring": t.monitoring, "valid": t.plan.valid} for t in get_service().store.list()]


@app.post("/trips", status_code=201)
def create_trip(payload: Preferences):
    return get_service().create(payload)


@app.post("/trip")
def compatibility_trip(payload: Preferences):
    return legacy_response(get_service().create(payload))


@app.get("/trips/{trip_id}")
def read_trip(trip_id: str):
    return get_service().store.get(trip_id)


@app.patch("/trips/{trip_id}")
def update_trip(trip_id: str, payload: TripUpdate):
    return get_service().update(trip_id, payload.version, payload.preferences, payload.monitoring)


@app.post("/trips/{trip_id}/refresh")
def refresh_trip(trip_id: str, payload: Versioned):
    service = get_service()
    return service.replan(service.checked(trip_id, payload.version), "Manual refresh")


@app.patch("/trips/{trip_id}/activities/{activity_id}")
def update_activity(trip_id: str, activity_id: str, payload: ActivityUpdate):
    changes = payload.model_dump(exclude={"version"}, exclude_none=True)
    return get_service().activity(trip_id, activity_id, payload.version, changes)


@app.post("/trips/{trip_id}/expenses")
def add_expense(trip_id: str, payload: ExpenseInput):
    return get_service().expense(trip_id, payload.version, payload.expense)


@app.post("/trips/{trip_id}/chat")
def chat(trip_id: str, payload: ChatInput):
    return get_service().chat(trip_id, payload.version, payload.message)


@app.post("/chat/draft")
def draft_chat(payload: DraftChat):
    return get_service().llm.chat(payload.message, payload.preferences)


@app.get("/trips/{trip_id}/revisions")
def revisions(trip_id: str):
    return get_service().store.history(trip_id)
