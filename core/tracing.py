"""Centralised OpenTelemetry tracing helpers.

Every Python component calls ``init_tracing`` once at startup.  The inject /
extract helpers allow propagation of W3C ``traceparent`` across non-HTTP
boundaries (UDP JSON payload, AMQP headers).
"""

from __future__ import annotations

import logging
import os
from collections.abc import Mapping
from typing import Any

from opentelemetry import context, trace
from opentelemetry.context import Context
from opentelemetry.propagators.textmap import (
    CarrierT,
    Getter,
    Setter,
    TextMapPropagator,
)
from opentelemetry.propagate import get_global_textmap, set_global_textmap
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

logger = logging.getLogger(__name__)

_TRACE_KEYS = ("traceparent", "tracestate")


class _DictGetter(Getter[dict[str, Any]]):
    def get(self, carrier: dict[str, Any], key: str) -> list[str] | None:
        val = carrier.get(key)
        if val is None:
            return None
        return [str(val)]

    def keys(self, carrier: dict[str, Any]) -> list[str]:
        return list(carrier.keys())


class _DictSetter(Setter[dict[str, Any]]):
    def set(self, carrier: dict[str, Any], key: str, value: str) -> None:
        carrier[key] = value


_dict_getter = _DictGetter()
_dict_setter = _DictSetter()


def init_tracing(service_name: str, otlp_endpoint: str | None = None) -> TracerProvider:
    """Create and register a global ``TracerProvider``.

    When *otlp_endpoint* is given the provider exports via OTLP/gRPC.
    Otherwise spans are dumped to the console (useful for local dev).
    """
    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    if otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
    else:
        exporter = ConsoleSpanExporter()

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    set_global_textmap(CompositePropagator([TraceContextTextMapPropagator()]))

    logger.info(
        "Tracing initialised: service=%s endpoint=%s",
        service_name,
        otlp_endpoint or "console",
    )
    return provider


def get_otlp_endpoint() -> str | None:
    """Read the OTLP endpoint from the environment (returns *None* when unset)."""
    return os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or None


def inject_into_dict(carrier: dict[str, Any]) -> None:
    """Inject the current span's trace context into a plain *dict*."""
    get_global_textmap().inject(carrier, setter=_DictSetter())


def extract_from_dict(carrier: dict[str, Any]) -> Context:
    """Extract trace context from a plain *dict* (e.g. a JSON object)."""
    return get_global_textmap().extract(carrier, getter=_DictGetter())


def inject_into_headers(headers: dict[str, str]) -> None:
    """Inject trace context into an AMQP-style *headers* dict."""
    get_global_textmap().inject(headers, setter=_DictSetter())


def extract_from_headers(headers: Mapping[str, Any]) -> Context:
    """Extract trace context from AMQP message headers."""
    flat: dict[str, Any] = dict(headers) if headers else {}
    return get_global_textmap().extract(flat, getter=_DictGetter())


def strip_trace_keys(obj: dict[str, Any]) -> None:
    """Remove injected trace fields from a dict so they don't leak into storage."""
    for key in _TRACE_KEYS:
        obj.pop(key, None)
