import logging

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from backend.config import BackendConfig
from backend.db import probe_database

router = APIRouter()
logger = logging.getLogger(__name__)


def get_backend_config(request: Request) -> BackendConfig:
    return request.app.state.config


def build_health_response(config: BackendConfig) -> JSONResponse:
    try:
        database_ok = probe_database(config)
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
def health_check(config: BackendConfig = Depends(get_backend_config)) -> JSONResponse:
    return build_health_response(config)
