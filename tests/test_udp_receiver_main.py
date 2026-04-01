from udp_receiver.main import _metrics_enabled, _start_metrics_server


def test_metrics_enabled_defaults_to_true():
    assert _metrics_enabled({}) is True


def test_start_metrics_server_uses_env_configuration(monkeypatch):
    calls: list[tuple[int, str]] = []

    def fake_start_http_server(port: int, addr: str = "0.0.0.0") -> None:
        calls.append((port, addr))

    monkeypatch.setattr("udp_receiver.main.start_http_server", fake_start_http_server)

    result = _start_metrics_server(
        {
            "PROMETHEUS_METRICS_HOST": "127.0.0.1",
            "PROMETHEUS_METRICS_PORT": "9200",
        }
    )

    assert result == ("127.0.0.1", 9200)
    assert calls == [(9200, "127.0.0.1")]


def test_start_metrics_server_can_be_disabled(monkeypatch):
    called = False

    def fake_start_http_server(port: int, addr: str = "0.0.0.0") -> None:
        nonlocal called
        called = True

    monkeypatch.setattr("udp_receiver.main.start_http_server", fake_start_http_server)

    result = _start_metrics_server({"PROMETHEUS_METRICS_ENABLED": "false"})

    assert result is None
    assert called is False
