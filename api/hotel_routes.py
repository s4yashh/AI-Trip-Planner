"""Separate HTTP routes for hotel suggestions. Stateless; nothing is booked or stored."""
from fastapi import APIRouter, HTTPException, Request

from models.hotels import HotelSearch
from services.hotel_suggestion_service import HotelSuggestionService
from services.live_providers import ProviderError


router = APIRouter(prefix="/hotels", tags=["hotels"])


def get_hotel_service(request: Request):
    if not hasattr(request.app.state, "hotel_suggestion_service"):
        request.app.state.hotel_suggestion_service = HotelSuggestionService()
    return request.app.state.hotel_suggestion_service


@router.post("/suggestions")
def hotel_suggestions(payload: HotelSearch, request: Request):
    try:
        return get_hotel_service(request).suggest(payload)
    except ProviderError as exc:
        status = 422 if "not found" in str(exc).lower() else 503
        raise HTTPException(status_code=status, detail=str(exc)) from exc
