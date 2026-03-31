import logging
import os
import sys

from opentelemetry import trace


class _TraceInjectFilter(logging.Filter):
    """Inject ``trace_id`` and ``span_id`` from the current OTel context."""

    def filter(self, record: logging.LogRecord) -> bool:
        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx and ctx.trace_id:
            record.trace_id = format(ctx.trace_id, "032x")
            record.span_id = format(ctx.span_id, "016x")
        else:
            record.trace_id = "0" * 32
            record.span_id = "0" * 16
        return True


def setup_logging(level: int = logging.INFO, json_format: bool | None = None) -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    if root_logger.handlers:
        return

    if json_format is None:
        json_format = os.environ.get("LOG_FORMAT", "").lower() == "json"

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    if json_format:
        from pythonjsonlogger.json import JsonFormatter

        formatter = JsonFormatter(
            fmt="%(asctime)s %(levelname)s %(name)s %(message)s "
            "%(trace_id)s %(span_id)s",
            rename_fields={
                "asctime": "timestamp",
                "levelname": "level",
            },
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    handler.setFormatter(formatter)
    handler.addFilter(_TraceInjectFilter())

    root_logger.addHandler(handler)
