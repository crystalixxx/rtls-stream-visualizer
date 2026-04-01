import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.consumer import on_message


def _make_pool():
    return MagicMock()


def _make_envelope_bytes(**overrides) -> bytes:
    payload = {
        "tag_id": "tag-001",
        "ts_utc_ms": 1700000000000,
        "source_type": "display",
        "status": None,
        "layer": 1,
        "area": "zone-A",
        "x": 10.5,
        "y": 20.3,
        "z": 0.0,
        "lng": None,
        "lat": None,
        "origin": "ls-1000",
        "raw_message": "display:...",
        "parse_warnings": [],
    }
    payload.update(overrides.pop("payload", {}))
    envelope = {
        "schema_version": "1.0",
        "event_type": "position",
        "origin": "ls-1000",
        "normalized": True,
        "ingested_at_ms": 1700000000100,
        "payload": payload,
    }
    envelope.update(overrides)
    return json.dumps(envelope).encode()


def _make_message(body: bytes) -> AsyncMock:
    msg = AsyncMock()
    msg.body = body
    msg.process = MagicMock(return_value=AsyncMock())
    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=None)
    ctx.__aexit__ = AsyncMock(return_value=False)
    msg.process.return_value = ctx
    return msg


class TestOnMessage:
    @pytest.mark.asyncio
    @patch("backend.consumer.get_connection")
    @patch("backend.consumer.persist_envelope")
    async def test_valid_message_persists_and_acks(self, mock_persist, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        body = _make_envelope_bytes()
        message = _make_message(body)
        loop = asyncio.get_event_loop()
        pool = _make_pool()

        await on_message(message, pool=pool, loop=loop)

        mock_persist.assert_called_once()
        call_args = mock_persist.call_args
        assert call_args[0][0] is mock_conn
        assert call_args[0][1]["schema_version"] == "1.0"
        assert call_args[0][1]["payload"]["tag_id"] == "tag-001"

    @pytest.mark.asyncio
    async def test_malformed_json_does_not_raise(self):
        message = _make_message(b"not-json{{{")
        loop = asyncio.get_event_loop()
        pool = _make_pool()

        await on_message(message, pool=pool, loop=loop)

    @pytest.mark.asyncio
    async def test_missing_tag_id_does_not_raise(self):
        envelope = {
            "schema_version": "1.0",
            "event_type": "position",
            "origin": "ls-1000",
            "normalized": True,
            "ingested_at_ms": 100,
            "payload": {"no_tag": True},
        }
        message = _make_message(json.dumps(envelope).encode())
        loop = asyncio.get_event_loop()
        pool = _make_pool()

        await on_message(message, pool=pool, loop=loop)

    @pytest.mark.asyncio
    @patch("backend.consumer.get_connection")
    @patch("backend.consumer.persist_envelope", side_effect=RuntimeError("db down"))
    async def test_db_error_propagates_for_requeue(self, mock_persist, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__ = MagicMock(return_value=mock_conn)
        mock_get_conn.return_value.__exit__ = MagicMock(return_value=False)

        body = _make_envelope_bytes()
        message = _make_message(body)
        loop = asyncio.get_event_loop()
        pool = _make_pool()

        with pytest.raises(RuntimeError, match="db down"):
            await on_message(message, pool=pool, loop=loop)
