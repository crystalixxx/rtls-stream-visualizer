import asyncio
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from psycopg_pool import ConnectionPool

from backend.broadcast import Broadcast
from backend.db import get_connection
from backend.metrics import WS_ACTIVE_CONNECTIONS
from backend.repository import get_all_current_positions

router = APIRouter()
logger = logging.getLogger(__name__)


def _snapshot(pool: ConnectionPool) -> list[dict]:
    with get_connection(pool) as conn:
        return get_all_current_positions(conn)


def _snapshot_timestamps(snapshot: list[dict]) -> dict[str, int]:
    """Build a map of tag_id -> ts_utc_ms from the snapshot."""
    return {row["tag_id"]: row["ts_utc_ms"] for row in snapshot if "tag_id" in row}


def _is_stale(envelope: dict, snapshot_ts: dict[str, int]) -> bool:
    """Return True if the envelope is older than what the snapshot already contains."""
    payload = envelope.get("payload", {})
    tag_id = payload.get("tag_id")
    ts = payload.get("ts_utc_ms")
    if tag_id is None or ts is None:
        return False
    return ts < snapshot_ts.get(tag_id, 0)


@router.websocket("/ws/positions")
async def positions_ws(websocket: WebSocket) -> None:
    pool: ConnectionPool = websocket.app.state.pool
    broadcast: Broadcast = websocket.app.state.broadcast

    await websocket.accept()
    WS_ACTIVE_CONNECTIONS.inc()

    queue = broadcast.subscribe()
    try:
        loop = asyncio.get_running_loop()
        snapshot = await loop.run_in_executor(None, _snapshot, pool)
        await websocket.send_json(snapshot)

        ts_map = _snapshot_timestamps(snapshot)

        while True:
            envelope = await queue.get()
            if _is_stale(envelope, ts_map):
                continue
            await websocket.send_json(envelope)
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    finally:
        broadcast.unsubscribe(queue)
        WS_ACTIVE_CONNECTIONS.dec()
