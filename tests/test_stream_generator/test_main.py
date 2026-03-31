import json
import types
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import stream_generator.main as sg_main
from core.tracing import init_tracing
from core.validate import ValidatedObject

init_tracing("test-stream-generator")


@pytest.fixture()
def _jsonl_file(tmp_path: Path) -> Path:
    data = [
        {"tag_id": "tag-1", "x": 1.0, "y": 2.0, "ts_utc_ms": 1000},
        {"tag_id": "tag-2", "x": 3.0, "y": 4.0, "ts_utc_ms": 2000},
    ]
    p = tmp_path / "test.jsonl"
    p.write_text("\n".join(json.dumps(d) for d in data), encoding="utf-8")
    return p


@pytest.fixture()
def _fake_config():
    return types.SimpleNamespace(
        validation=types.SimpleNamespace(
            schema_path="config/ls_1000_scheme.json", origin="ls-1000"
        ),
    )


def test_main_sends_validated_objects_via_udp(_jsonl_file: Path, _fake_config):
    validated = [
        ValidatedObject(origin="ls-1000", data={"tag_id": "tag-1", "x": 1.0}),
        ValidatedObject(origin="ls-1000", data={"tag_id": "tag-2", "x": 3.0}),
    ]
    mock_validator = MagicMock()
    mock_validator.get_validated_objects_from_file.return_value = (validated, [])

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(sg_main, "get_config", return_value=_fake_config),
        patch.object(sg_main, "Validator", return_value=mock_validator),
        patch.object(sg_main, "UdpClient", return_value=mock_client),
        patch.object(sg_main, "init_tracing"),
    ):
        sg_main.main(
            source=_jsonl_file,
            ip="127.0.0.1",
            port=9999,
            batch_size=10,
            time_between_batches=0,
        )

    mock_client.send.assert_called_once()
    sent_objects = mock_client.send.call_args[0][0]
    assert len(sent_objects) == 2
    assert all("traceparent" in obj for obj in sent_objects)


def test_main_logs_validation_errors(_jsonl_file: Path, _fake_config):
    mock_validator = MagicMock()
    mock_validator.get_validated_objects_from_file.return_value = ([], ["error1"])

    mock_client = MagicMock()
    mock_client.__enter__ = MagicMock(return_value=mock_client)
    mock_client.__exit__ = MagicMock(return_value=False)

    with (
        patch.object(sg_main, "get_config", return_value=_fake_config),
        patch.object(sg_main, "Validator", return_value=mock_validator),
        patch.object(sg_main, "UdpClient", return_value=mock_client),
        patch.object(sg_main, "init_tracing"),
        patch.object(sg_main, "logger") as mock_logger,
    ):
        sg_main.main(
            source=_jsonl_file,
            ip="127.0.0.1",
            port=9999,
            batch_size=10,
            time_between_batches=0,
        )

    mock_logger.error.assert_called_once()
    mock_client.send.assert_called_once()
    assert mock_client.send.call_args[0][0] == []
