"""Group-trip lifecycle, isolated from the existing single-trip service."""
from uuid import uuid4

from agents.group_trip_agent import GroupTripAgent
from models.group_trip import GroupMember, GroupMemberPreferences, GroupTrip, GroupTripCreate
from services.group_trip_store import GroupTripConflict, GroupTripStore


class GroupTripService:
    def __init__(self, store=None, planner=None):
        self.store = store or GroupTripStore()
        self.planner = planner or GroupTripAgent()

    def create(self, request: GroupTripCreate):
        group = GroupTrip(
            destination=request.destination,
            start_date=request.start_date,
            number_of_days=request.number_of_days,
            member_count=request.member_count,
            currency=request.currency,
            members=[GroupMember(id=str(uuid4()), name=f"Member {i + 1}")
                     for i in range(request.member_count)],
        )
        return self.store.create(group)

    def member_preferences(self, group_id, member_id, version, preferences: GroupMemberPreferences):
        group = self.checked(group_id, version)
        member = next((item for item in group.members if item.id == member_id), None)
        if member is None:
            raise KeyError(member_id)
        member.preferences = preferences
        group.plan = None
        return self.store.save(group, version)

    def generate(self, group_id, version):
        group = self.checked(group_id, version)
        if any(member.preferences is None for member in group.members):
            raise ValueError("Save preferences for every member before generating the group plan.")
        group.plan = self.planner.run(group)
        return self.store.save(group, version)

    def checked(self, group_id, version):
        group = self.store.get(group_id)
        if group.version != version:
            raise GroupTripConflict("Group trip changed. Reload it before continuing.")
        return group
