from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Any

from psycopg import Connection
from psycopg_pool import ConnectionPool

from backend.config import BackendConfig

logger = logging.getLogger(__name__)

_MIN_POOL_SIZE = 4
_MAX_POOL_SIZE = 20
_POOL_TIMEOUT = 10.0


def create_pool(config: BackendConfig) -> ConnectionPool:
    """Create a connection pool.

    The pool populates connections in the background, so the caller is
    not blocked when PostgreSQL is temporarily unreachable.  The first
    request that actually needs a connection will wait up to *timeout*
    seconds for one to become available.
    """
    pool = ConnectionPool(
        conninfo=config.database.dsn,
        min_size=_MIN_POOL_SIZE,
        max_size=_MAX_POOL_SIZE,
        timeout=_POOL_TIMEOUT,
    )
    logger.info(
        "Connection pool created (lazy): min=%d max=%d timeout=%.1fs",
        _MIN_POOL_SIZE,
        _MAX_POOL_SIZE,
        _POOL_TIMEOUT,
    )
    return pool


@contextmanager
def get_connection(pool: ConnectionPool):
    """Borrow a connection from the pool; returns it automatically on exit."""
    with pool.connection() as conn:
        yield conn


def probe_database(pool: ConnectionPool) -> bool:
    with get_connection(pool) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

    return result == (1,)
