from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter

from core.tracing import (
    extract_from_dict,
    extract_from_headers,
    init_tracing,
    inject_into_dict,
    inject_into_headers,
    strip_trace_keys,
)


def _setup_provider() -> TracerProvider:
    """Ensure a deterministic provider is active for tests."""
    provider = init_tracing("test-service")
    return provider


class TestInjectExtractDict:
    def test_inject_adds_traceparent(self):
        _setup_provider()
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("test-span"):
            carrier: dict = {}
            inject_into_dict(carrier)

            assert "traceparent" in carrier
            assert carrier["traceparent"].startswith("00-")

    def test_round_trip(self):
        _setup_provider()
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("parent"):
            carrier: dict = {}
            inject_into_dict(carrier)
            original_traceparent = carrier["traceparent"]

        ctx = extract_from_dict(carrier)
        assert ctx is not None

        span = trace.get_current_span(ctx)
        if span and span.get_span_context().trace_id:
            parts = original_traceparent.split("-")
            assert format(span.get_span_context().trace_id, "032x") == parts[1]

    def test_extract_empty_dict_does_not_raise(self):
        _setup_provider()
        ctx = extract_from_dict({})
        assert ctx is not None


class TestInjectExtractHeaders:
    def test_inject_adds_traceparent(self):
        _setup_provider()
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("test-span"):
            headers: dict = {}
            inject_into_headers(headers)

            assert "traceparent" in headers

    def test_round_trip_headers(self):
        _setup_provider()
        tracer = trace.get_tracer("test")
        with tracer.start_as_current_span("parent"):
            headers: dict = {}
            inject_into_headers(headers)
            original = headers["traceparent"]

        ctx = extract_from_headers(headers)
        assert ctx is not None
        span = trace.get_current_span(ctx)
        if span and span.get_span_context().trace_id:
            parts = original.split("-")
            assert format(span.get_span_context().trace_id, "032x") == parts[1]

    def test_extract_empty_headers(self):
        _setup_provider()
        ctx = extract_from_headers({})
        assert ctx is not None

    def test_extract_none_headers(self):
        _setup_provider()
        ctx = extract_from_headers(None)
        assert ctx is not None


class TestStripTraceKeys:
    def test_removes_traceparent_and_tracestate(self):
        d = {"traceparent": "00-abc-def-01", "tracestate": "x=y", "tag_id": "t1"}
        strip_trace_keys(d)
        assert "traceparent" not in d
        assert "tracestate" not in d
        assert d["tag_id"] == "t1"

    def test_no_error_on_missing_keys(self):
        d = {"tag_id": "t1"}
        strip_trace_keys(d)
        assert d == {"tag_id": "t1"}


class TestInitTracing:
    def test_returns_tracer_provider(self):
        provider = init_tracing("my-service")
        assert isinstance(provider, TracerProvider)

    def test_sets_global_provider(self):
        init_tracing("my-service")
        provider = trace.get_tracer_provider()
        assert provider is not None
