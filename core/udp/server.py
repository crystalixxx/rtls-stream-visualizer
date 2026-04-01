import logging
import json
import socket
import time
from dataclasses import asdict
from collections.abc import Callable

from opentelemetry import context as otel_context, trace

from core.broker.interface import BrockerPublisher
from core.envelope import (
    EnvelopeContext,
    EnvelopeRegistry,
    create_default_envelope_registry,
)
from core.tracing import (
    extract_from_dict,
    inject_into_headers,
    strip_trace_keys,
)
from core.validate import Validator
from stream_handler import LS1000Parser, JsonStreamNormalizer

logger = logging.getLogger(__name__)

_tracer = trace.get_tracer(__name__)


class UdpServer:
    def __init__(
        self,
        ip: str,
        port: int,
        publisher: BrockerPublisher,
        topic: str,
        max_datagram_bytes: int = 64 * 1024,
        validator: Validator | None = None,
        parser: LS1000Parser | None = None,
        json_normalizer: JsonStreamNormalizer | None = None,
        envelope_version: str = "1.0",
        envelope_registry: EnvelopeRegistry | None = None,
        event_type: str = "position",
        on_decode_error: Callable[[bytes, Exception], None] | None = None,
    ):
        self.ip = ip
        self.port = port
        self.publisher = publisher
        self.topic = topic
        self.max_datagram_bytes = max_datagram_bytes
        self.validator = validator
        self.parser = parser
        self.json_normalizer = json_normalizer
        self.envelope_version = envelope_version
        self.envelope_registry = envelope_registry or create_default_envelope_registry()
        self.event_type = event_type
        self.on_decode_error = on_decode_error

        logger.info(f"Creating UDP server {self.ip}:{self.port}")

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.bind((self.ip, self.port))

    def serve_forever(self) -> None:
        while True:
            try:
                data, addr = self.socket.recvfrom(self.max_datagram_bytes)
            except OSError:
                break

            try:
                headers = {"source_ip": addr[0], "source_port": str(addr[1])}
                parent_ctx = self._extract_trace_context(data)
                token = otel_context.attach(parent_ctx) if parent_ctx else None
                try:
                    with _tracer.start_as_current_span(
                        "process_datagram",
                        attributes={
                            "net.peer.ip": addr[0],
                            "net.peer.port": addr[1],
                        },
                    ):
                        obj = self._process_datagram(data, headers)
                        envelope = self._build_envelope(obj, headers)
                        inject_into_headers(headers)
                        message = self._serialize_message(envelope)
                        self._publish_message(message, headers)
                finally:
                    if token is not None:
                        otel_context.detach(token)
            except Exception as exc:
                self._handle_processing_error(data, exc)

    def _extract_trace_context(self, data: bytes):
        """Best-effort extraction of W3C trace context from a JSON datagram."""
        try:
            obj = json.loads(data)
            if isinstance(obj, dict) and "traceparent" in obj:
                return extract_from_dict(obj)
        except Exception:
            pass
        return None

    def _process_datagram(self, data: bytes, headers: dict[str, str]):
        decoded = data.decode("utf-8")
        ls1000_obj = self._try_parse_ls1000(decoded, headers)
        if ls1000_obj is not None:
            return ls1000_obj
        return self._normalize_json_payload(decoded, headers)

    def _try_parse_ls1000(self, decoded: str, headers: dict[str, str]):
        if self.parser is None:
            return None

        parsed, parse_error = self.parser.parse_message(decoded)
        if parsed is None:
            logger.debug(
                "LS-1000 parser skipped message code=%s reason=%s",
                parse_error.code if parse_error else "unknown",
                parse_error.message if parse_error else "unknown",
            )
            return None

        headers["origin"] = "ls-1000"
        headers["parser"] = "ls1000"
        return asdict(parsed)

    def _normalize_json_payload(self, decoded: str, headers: dict[str, str]):
        raw_json = None
        origin = "json"
        cleaned = self._strip_trace_from_string(decoded)
        if self.validator is not None:
            validated, errors = self.validator.get_validated_object(cleaned, line_no=1)
            if validated is None:
                raise ValueError(f"Validation failed: {errors}")
            raw_json = validated.data
            origin = validated.origin
        else:
            raw_json = json.loads(cleaned)

        headers["origin"] = origin
        if self.json_normalizer is None:
            return raw_json

        normalized = self.json_normalizer.normalize(raw_json, raw_message=decoded)
        if normalized is None:
            raise ValueError(
                "JSON normalizer failed to map message into normalized payload"
            )

        headers["parser"] = "json-normalizer"
        return asdict(normalized)

    @staticmethod
    def _strip_trace_from_string(decoded: str) -> str:
        """Remove ``traceparent``/``tracestate`` from a JSON string before validation.

        This prevents ``additionalProperties: false`` schemas from rejecting
        payloads that carry injected W3C trace context fields.
        """
        try:
            obj = json.loads(decoded)
            if isinstance(obj, dict):
                strip_trace_keys(obj)
                return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass
        return decoded

    @staticmethod
    def _serialize_message(obj) -> bytes:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )

    def _build_envelope(self, payload, headers: dict[str, str]) -> dict:
        origin = "unknown"
        if isinstance(payload, dict):
            origin = headers.get("origin", payload.get("origin", "unknown"))
        context = EnvelopeContext(
            schema_version=self.envelope_version,
            event_type=self.event_type,
            origin=origin,
            normalized=isinstance(payload, dict)
            and "tag_id" in payload
            and "ts_utc_ms" in payload,
            ingested_at_ms=int(time.time() * 1000),
        )
        builder = self.envelope_registry.get(self.envelope_version)
        return builder.build(payload, context)

    def _publish_message(self, message: bytes, headers: dict[str, str]) -> None:
        logger.debug(
            "Sending into %s message_len=%s message_type=%s headers=%s",
            self.topic,
            len(message),
            type(message).__name__,
            headers,
        )
        self.publisher.publish(self.topic, message, headers=headers)

    def _handle_processing_error(self, data: bytes, exc: Exception) -> None:
        logger.error("UDP message processing failed: %s", exc)
        if self.on_decode_error:
            self.on_decode_error(data, exc)

    def close(self) -> None:
        logger.info(f"Closing UDP server {self.ip}:{self.port}")

        self.socket.close()
