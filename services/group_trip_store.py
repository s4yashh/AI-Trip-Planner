"""Dedicated SQLite persistence for group trips; never alters single-trip tables."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from models.group_trip import GroupTrip
from models.live import utcnow


class GroupTripConflict(Exception):
    pass


class GroupTripStore:
    def __init__(self, path=None):
        self.path = str(path or os.getenv("GROUP_TRIP_DB_PATH", "data/group_trips.sqlite3"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS group_trips (
                id TEXT PRIMARY KEY, version INTEGER NOT NULL, document TEXT NOT NULL
            )""")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        try:
            with db:
                yield db
        finally:
            db.close()

    def create(self, group):
        with self.connect() as db:
            db.execute("INSERT INTO group_trips VALUES (?, ?, ?)",
                       (group.id, group.version, group.model_dump_json()))
        return group

    def get(self, group_id):
        with self.connect() as db:
            row = db.execute("SELECT document FROM group_trips WHERE id=?", (group_id,)).fetchone()
        if row is None:
            raise KeyError(group_id)
        return GroupTrip.model_validate_json(row[0])

    def save(self, group, expected_version):
        updated = group.model_copy(deep=True)
        updated.version = expected_version + 1
        updated.updated_at = utcnow()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute("UPDATE group_trips SET version=?, document=? WHERE id=? AND version=?",
                                (updated.version, updated.model_dump_json(), updated.id, expected_version))
            if cursor.rowcount != 1:
                raise GroupTripConflict("Group trip changed. Reload it and try again.")
        return updated
