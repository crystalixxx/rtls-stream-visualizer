import logging

from fastapi import APIRouter, Depends, Query, Request

from backend.api.schemas import PositionHistoryResponse, PositionOut
from backend.config import BackendConfig
from backend.db import get_connection
from backend.repository import count_position_history, get_position_history

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_config(request: Request) -> BackendConfig:
    return request.app.state.config


@router.get("/positions/history", response_model=PositionHistoryResponse)
def position_history(
    tag_id: str = Query(..., description="Tag identifier"),
    from_ts: int | None = Query(None, description="Start timestamp (ms UTC)"),
    to_ts: int | None = Query(None, description="End timestamp (ms UTC)"),
    limit: int = Query(100, ge=1, le=1000, description="Page size"),
    offset: int = Query(0, ge=0, description="Page offset"),
    config: BackendConfig = Depends(_get_config),
) -> PositionHistoryResponse:
    with get_connection(config) as conn:
        rows = get_position_history(conn, tag_id, from_ts, to_ts, limit, offset)
        total = count_position_history(conn, tag_id, from_ts, to_ts)

    items = [PositionOut(**row) for row in rows]
    return PositionHistoryResponse(items=items, total=total)
