import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.broadcast import Broadcast
from backend.config import BackendConfig
from backend.db import get_connection
from backend.repository import get_all_current_positions

router = APIRouter()
logger = logging.getLogger(__name__)


def _snapshot(config: BackendConfig) -> list[dict]:
    with get_connection(config) as conn:
        return get_all_current_positions(conn)


@router.websocket("/ws/positions")
async def positions_ws(websocket: WebSocket) -> None:
    config: BackendConfig = websocket.app.state.config
    broadcast: Broadcast = websocket.app.state.broadcast

    await websocket.accept()

    snapshot = _snapshot(config)
    await websocket.send_json(snapshot)

    queue = broadcast.subscribe()
    try:
        while True:
            envelope = await queue.get()
            await websocket.send_json(envelope)
    except WebSocketDisconnect:
        logger.debug("WebSocket client disconnected")
    finally:
        broadcast.unsubscribe(queue)
