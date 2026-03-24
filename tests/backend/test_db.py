from backend.config import BackendConfig, ApiConfig, DatabaseConfig
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
        self.closed = False
        self.cursor_instance = DummyCursor(result=result)

    def cursor(self):
        return self.cursor_instance

    def close(self):
        self.closed = True


def _config() -> BackendConfig:
    return BackendConfig(
        api=ApiConfig(host="127.0.0.1", port=8000),
        database=DatabaseConfig(dsn="postgresql://postgres:postgres@localhost:5432/db"),
    )


def test_get_connection_closes_connection():
    connection = DummyConnection()

    with get_connection(_config(), connection_factory=lambda _: connection) as current:
        assert current is connection
        assert connection.closed is False

    assert connection.closed is True


def test_probe_database_returns_true_for_successful_probe():
    connection = DummyConnection(result=(1,))

    result = probe_database(_config(), connection_factory=lambda _: connection)

    assert result is True
    assert connection.cursor_instance.executed == ["SELECT 1"]


def test_probe_database_returns_false_for_unexpected_result():
    connection = DummyConnection(result=(0,))

    result = probe_database(_config(), connection_factory=lambda _: connection)

    assert result is False
