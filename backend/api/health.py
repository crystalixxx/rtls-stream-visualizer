import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse
from psycopg_pool import ConnectionPool

from backend.db import probe_database

router = APIRouter()
logger = logging.getLogger(__name__)


def _get_pool(request: Request) -> ConnectionPool:
    return request.app.state.pool


def build_health_response(pool: ConnectionPool) -> JSONResponse:
    try:
        database_ok = probe_database(pool)
    except Exception as exc:
        logger.error("Database health probe failed: %s", exc)
        database_ok = False

    if database_ok:
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"status": "ok", "database": "ok"},
        )

    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "degraded", "database": "unavailable"},
    )


@router.get("/health")
def health_check(pool: ConnectionPool = Depends(_get_pool)) -> JSONResponse:
    return build_health_response(pool)
