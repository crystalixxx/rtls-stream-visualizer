import json
import logging
from typing import Any

from psycopg import Connection

from backend.repository.queries import load_sql

logger = logging.getLogger(__name__)


def _extract_params(envelope: dict[str, Any]) -> dict[str, Any]:
    payload = envelope.get("payload", {})
    warnings = payload.get("parse_warnings", [])
    return {
        "schema_version": envelope["schema_version"],
        "event_type": envelope["event_type"],
        "origin": envelope["origin"],
        "normalized": envelope["normalized"],
        "ingested_at_ms": envelope["ingested_at_ms"],
        "tag_id": payload["tag_id"],
        "ts_utc_ms": payload["ts_utc_ms"],
        "source_type": payload.get("source_type", "unknown"),
        "status": payload.get("status"),
        "layer": payload.get("layer"),
        "area": payload.get("area"),
        "x": payload.get("x"),
        "y": payload.get("y"),
        "z": payload.get("z"),
        "lng": payload.get("lng"),
        "lat": payload.get("lat"),
        "raw_message": payload.get("raw_message", ""),
        "parse_warnings": json.dumps(warnings),
    }


def insert_position_event(
    connection: Connection[Any], envelope: dict[str, Any]
) -> None:
    params = _extract_params(envelope)
    with connection.cursor() as cursor:
        cursor.execute(load_sql("insert_position_event"), params)


def upsert_current_position(
    connection: Connection[Any], envelope: dict[str, Any]
) -> None:
    params = _extract_params(envelope)
    with connection.cursor() as cursor:
        cursor.execute(load_sql("upsert_current_position"), params)


def persist_envelope(connection: Connection[Any], envelope: dict[str, Any]) -> None:
    """Insert event and upsert current position in a single transaction."""
    insert_position_event(connection, envelope)
    upsert_current_position(connection, envelope)
    connection.commit()
    logger.debug(
        "Persisted envelope for tag_id=%s",
        envelope.get("payload", {}).get("tag_id"),
    )


_CURRENT_POS_COLUMNS = (
    "tag_id",
    "ts_utc_ms",
    "source_type",
    "status",
    "layer",
    "area",
    "x",
    "y",
    "z",
    "lng",
    "lat",
    "origin",
)

_HISTORY_COLUMNS = _CURRENT_POS_COLUMNS


def get_all_current_positions(connection: Connection[Any]) -> list[dict[str, Any]]:
    with connection.cursor() as cursor:
        cursor.execute(load_sql("select_all_current_positions"))
        rows = cursor.fetchall()
    return [dict(zip(_CURRENT_POS_COLUMNS, row)) for row in rows]


def _build_time_filters(
    from_ts: int | None, to_ts: int | None
) -> tuple[str, dict[str, Any]]:
    clauses = ""
    params: dict[str, Any] = {}
    if from_ts is not None:
        clauses += " AND ts_utc_ms >= %(from_ts)s"
        params["from_ts"] = from_ts
    if to_ts is not None:
        clauses += " AND ts_utc_ms <= %(to_ts)s"
        params["to_ts"] = to_ts
    return clauses, params


def get_position_history(
    connection: Connection[Any],
    tag_id: str,
    from_ts: int | None,
    to_ts: int | None,
    limit: int,
    offset: int,
) -> list[dict[str, Any]]:
    time_clauses, time_params = _build_time_filters(from_ts, to_ts)
    base = load_sql("select_position_history")
    query = base.replace("ORDER BY", f"{time_clauses}\nORDER BY")
    params: dict[str, Any] = {"tag_id": tag_id, "limit": limit, "offset": offset}
    params.update(time_params)
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
    return [dict(zip(_HISTORY_COLUMNS, row)) for row in rows]


def count_position_history(
    connection: Connection[Any],
    tag_id: str,
    from_ts: int | None,
    to_ts: int | None,
) -> int:
    time_clauses, time_params = _build_time_filters(from_ts, to_ts)
    base = load_sql("count_position_history")
    query = base + time_clauses
    params: dict[str, Any] = {"tag_id": tag_id}
    params.update(time_params)
    with connection.cursor() as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
    return row[0] if row else 0
