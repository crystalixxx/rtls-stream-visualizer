from unittest.mock import MagicMock, patch

from backend.db import get_connection, probe_database


class DummyCursor:
    def __init__(self, result=(1,)):
        self.result = result
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, query):
        self.executed.append(query)

    def fetchone(self):
        return self.result


class DummyConnection:
    def __init__(self, result=(1,)):
        self.cursor_instance = DummyCursor(result=result)

    def cursor(self):
        return self.cursor_instance


def _make_pool(conn):
    """Create a mock pool that yields the given connection."""
    pool = MagicMock()
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=conn)
    ctx.__exit__ = MagicMock(return_value=False)
    pool.connection.return_value = ctx
    return pool


def test_get_connection_returns_connection_from_pool():
    conn = DummyConnection()
    pool = _make_pool(conn)

    with get_connection(pool) as current:
        assert current is conn

    pool.connection.assert_called_once()


def test_probe_database_returns_true_for_successful_probe():
    conn = DummyConnection(result=(1,))
    pool = _make_pool(conn)

    result = probe_database(pool)

    assert result is True
    assert conn.cursor_instance.executed == ["SELECT 1"]


def test_probe_database_returns_false_for_unexpected_result():
    conn = DummyConnection(result=(0,))
    pool = _make_pool(conn)

    result = probe_database(pool)

    assert result is False
