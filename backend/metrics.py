"""Prometheus metric definitions for the backend service."""

from prometheus_client import Counter, Gauge, Histogram

HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
)

WS_ACTIVE_CONNECTIONS = Gauge(
    "ws_active_connections",
    "Number of active WebSocket connections",
)

CONSUMER_MESSAGES_PROCESSED = Counter(
    "consumer_messages_processed_total",
    "Total messages successfully processed by the consumer",
)

CONSUMER_MESSAGES_FAILED = Counter(
    "consumer_messages_failed_total",
    "Total messages that failed processing",
    ["reason"],
)

DB_WRITE_LATENCY = Histogram(
    "db_write_duration_seconds",
    "Database write latency in seconds",
)
