import json

import pytest

from backend.repository import (
    insert_position_event,
    upsert_current_position,
    persist_envelope,
)
from backend.repository.positions import _extract_params
from backend.repository.queries import load_sql


def _make_envelope(**overrides):
    payload = {
        "tag_id": "tag-001",
        "ts_utc_ms": 1700000000000,
        "source_type": "display",
        "status": None,
        "layer": 1,
        "area": "zone-A",
        "x": 10.5,
        "y": 20.3,
        "z": 0.0,
        "lng": None,
        "lat": None,
        "origin": "ls-1000",
        "raw_message": "display:...",
        "parse_warnings": [],
    }
    payload.update(overrides.pop("payload", {}))
    envelope = {
        "schema_version": "1.0",
        "event_type": "position",
        "origin": "ls-1000",
        "normalized": True,
        "ingested_at_ms": 1700000000100,
        "payload": payload,
    }
    envelope.update(overrides)
    return envelope


class TestExtractParams:
    def test_extracts_all_fields_from_envelope(self):
        envelope = _make_envelope()
        params = _extract_params(envelope)

        assert params["schema_version"] == "1.0"
        assert params["event_type"] == "position"
        assert params["origin"] == "ls-1000"
        assert params["normalized"] is True
        assert params["ingested_at_ms"] == 1700000000100
        assert params["tag_id"] == "tag-001"
        assert params["ts_utc_ms"] == 1700000000000
        assert params["source_type"] == "display"
        assert params["x"] == 10.5
        assert params["y"] == 20.3
        assert params["z"] == 0.0
        assert params["layer"] == 1
        assert params["area"] == "zone-A"
        assert params["raw_message"] == "display:..."
        assert params["parse_warnings"] == "[]"

    def test_serializes_parse_warnings_as_json(self):
        envelope = _make_envelope(payload={"parse_warnings": ["warn1", "warn2"]})
        params = _extract_params(envelope)

        assert params["parse_warnings"] == json.dumps(["warn1", "warn2"])

    def test_defaults_source_type_to_unknown(self):
        envelope = _make_envelope()
        del envelope["payload"]["source_type"]
        params = _extract_params(envelope)

        assert params["source_type"] == "unknown"


class DummyCursor:
    def __init__(self):
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, query, params=None):
        self.executed.append((query, params))


class DummyConnection:
    def __init__(self):
        self._cursor = DummyCursor()
        self.committed = False

    def cursor(self):
        return self._cursor

    def commit(self):
        self.committed = True


class TestInsertPositionEvent:
    def test_executes_insert_with_correct_params(self):
        conn = DummyConnection()
        envelope = _make_envelope()

        insert_position_event(conn, envelope)

        assert len(conn._cursor.executed) == 1
        sql, params = conn._cursor.executed[0]
        assert "INSERT INTO position_events" in sql
        assert params["tag_id"] == "tag-001"
        assert params["schema_version"] == "1.0"


class TestUpsertCurrentPosition:
    def test_executes_upsert_with_on_conflict(self):
        conn = DummyConnection()
        envelope = _make_envelope()

        upsert_current_position(conn, envelope)

        assert len(conn._cursor.executed) == 1
        sql, params = conn._cursor.executed[0]
        assert "INSERT INTO current_positions" in sql
        assert "ON CONFLICT (tag_id) DO UPDATE" in sql
        assert params["tag_id"] == "tag-001"

    def test_upsert_has_recency_guard(self):
        sql = load_sql("upsert_current_position")

        assert "WHERE EXCLUDED.ts_utc_ms >= current_positions.ts_utc_ms" in sql


class TestPersistEnvelope:
    def test_inserts_event_and_upserts_current_then_commits(self):
        conn = DummyConnection()
        envelope = _make_envelope()

        persist_envelope(conn, envelope)

        assert len(conn._cursor.executed) == 2
        assert "position_events" in conn._cursor.executed[0][0]
        assert "current_positions" in conn._cursor.executed[1][0]
        assert conn.committed is True


class TestLoadSql:
    def test_loads_insert_position_event(self):
        sql = load_sql("insert_position_event")

        assert "INSERT INTO position_events" in sql
        assert "%(tag_id)s" in sql

    def test_loads_upsert_current_position(self):
        sql = load_sql("upsert_current_position")

        assert "INSERT INTO current_positions" in sql
        assert "ON CONFLICT (tag_id) DO UPDATE" in sql

    def test_raises_for_missing_file(self):
        with pytest.raises(FileNotFoundError):
            load_sql("nonexistent_query")
