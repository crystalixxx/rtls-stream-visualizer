from collections.abc import Callable
from contextlib import contextmanager
from typing import Any

from psycopg import Connection

from backend.config import BackendConfig

ConnectionFactory = Callable[[str], Connection[Any]]


def create_connection_factory() -> ConnectionFactory:
    return Connection.connect


@contextmanager
def get_connection(
    config: BackendConfig,
    connection_factory: ConnectionFactory | None = None,
):
    factory = connection_factory or create_connection_factory()
    connection = factory(config.database.dsn)
    try:
        yield connection
    finally:
        connection.close()


def probe_database(
    config: BackendConfig,
    connection_factory: ConnectionFactory | None = None,
) -> bool:
    with get_connection(config, connection_factory) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()

    return result == (1,)
