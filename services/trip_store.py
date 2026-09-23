"""SQLite aggregate store with atomic compare-and-swap and revision history."""
import json
import os
import sqlite3
from pathlib import Path

from models.live import Trip, utcnow


class ConflictError(Exception):
    pass


class TripStore:
    def __init__(self, path=None):
        self.path = str(path or os.getenv("TRIP_DB_PATH", "data/trips.sqlite3"))
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS trips (
                    id TEXT PRIMARY KEY, version INTEGER NOT NULL, document TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    trip_id TEXT NOT NULL, version INTEGER NOT NULL, created_at TEXT NOT NULL,
                    reason TEXT NOT NULL, before_json TEXT, after_json TEXT NOT NULL,
                    PRIMARY KEY (trip_id, version)
                );
            """)

    def connect(self):
        return sqlite3.connect(self.path, timeout=10)

    def get(self, trip_id):
        with self.connect() as db:
            row = db.execute("SELECT document FROM trips WHERE id=?", (trip_id,)).fetchone()
        if row is None:
            raise KeyError(trip_id)
        return Trip.model_validate_json(row[0])

    def list(self):
        with self.connect() as db:
            rows = db.execute("SELECT document FROM trips ORDER BY rowid DESC").fetchall()
        return [Trip.model_validate_json(row[0]) for row in rows]

    def create(self, trip):
        with self.connect() as db:
            db.execute("INSERT INTO trips VALUES (?, ?, ?)", (trip.id, 1, trip.model_dump_json()))
            db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?, ?)",
                       (trip.id, 1, utcnow(), "Trip created", None, trip.model_dump_json()))
        return trip

    def save(self, trip, expected_version, reason, revision=True):
        updated = trip.model_copy(deep=True)
        updated.version = expected_version + 1
        updated.updated_at = utcnow()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT document FROM trips WHERE id=? AND version=?",
                             (trip.id, expected_version)).fetchone()
            if row is None:
                raise ConflictError("Trip changed while this request ran. Reload and try again.")
            db.execute("UPDATE trips SET version=?, document=? WHERE id=?",
                       (updated.version, updated.model_dump_json(), trip.id))
            if revision:
                db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?, ?)",
                           (trip.id, updated.version, utcnow(), reason, row[0], updated.model_dump_json()))
        return updated

    def history(self, trip_id):
        self.get(trip_id)
        with self.connect() as db:
            rows = db.execute("SELECT version, created_at, reason, before_json, after_json "
                              "FROM revisions WHERE trip_id=? ORDER BY version DESC", (trip_id,)).fetchall()
        return [{"version": v, "created_at": t, "reason": r,
                 "before": json.loads(b) if b else None, "after": json.loads(a)} for v, t, r, b, a in rows]
