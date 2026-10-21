"""Separate HTTP routes for local group-trip planning."""
from fastapi import APIRouter, HTTPException, Request

from models.group_trip import GroupMemberUpdate, GroupTripCreate, GroupTripVersion
from services.group_trip_service import GroupTripService
from services.group_trip_store import GroupTripConflict


router = APIRouter(prefix="/group-trips", tags=["group trips"])


def get_group_service(request: Request):
    if not hasattr(request.app.state, "group_trip_service"):
        request.app.state.group_trip_service = GroupTripService()
    return request.app.state.group_trip_service


@router.post("", status_code=201)
def create_group_trip(payload: GroupTripCreate, request: Request):
    return get_group_service(request).create(payload)


@router.get("/{group_id}")
def read_group_trip(group_id: str, request: Request):
    try:
        return get_group_service(request).store.get(group_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Group trip not found.") from exc


@router.patch("/{group_id}/members/{member_id}")
def save_member_preferences(group_id: str, member_id: str, payload: GroupMemberUpdate,
                            request: Request):
    try:
        return get_group_service(request).member_preferences(
            group_id, member_id, payload.version, payload.preferences)
    except GroupTripConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Group trip or member not found.") from exc


@router.post("/{group_id}/plan")
def generate_group_plan(group_id: str, payload: GroupTripVersion, request: Request):
    try:
        return get_group_service(request).generate(group_id, payload.version)
    except GroupTripConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Group trip not found.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
