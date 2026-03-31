import copy
import logging

import typer
from opentelemetry import trace
from pathlib import Path

from core.logging_config import setup_logging
from core.config import load_config, get_config
from core.tracing import get_otlp_endpoint, init_tracing, inject_into_dict
from core.validate import Validator
from core.udp.client import UdpClient

logger = logging.getLogger(__name__)

tracer = trace.get_tracer(__name__)


def init():
    setup_logging()
    load_config()
    init_tracing("stream-generator", get_otlp_endpoint())
    logger.info("Application starting")


def main(
    source: Path = typer.Option(..., help="The path to the source JSONL file"),
    ip: str = typer.Option(..., help="The IP address of the destination"),
    port: int = typer.Option(..., help="The port of the destination"),
    batch_size: int = typer.Option(
        ..., help="The number of objects to send in each batch"
    ),
    time_between_batches: int = typer.Option(
        1, help="The time between batches in seconds"
    ),
):
    """
    Generate a stream of data from a source (JSONL file) and write it to a destination (IP:Port) using a UDP connection.
    """

    config = get_config()
    validator = Validator(config.validation.schema_path, config.validation.origin)
    objects, errors = validator.get_validated_objects_from_file(source)

    if errors:
        logger.error("Validation errors: %s", errors)

    raw_objects = [obj.data for obj in objects]

    with UdpClient(ip, port) as udp_client:
        with tracer.start_as_current_span(
            "generate_stream",
            attributes={"udp.host": ip, "udp.port": port, "batch.size": batch_size},
        ):
            traced_objects = _inject_trace_context(raw_objects)
            udp_client.send(traced_objects, batch_size, time_between_batches)

    logger.info("Stream generated successfully")


def _inject_trace_context(objects: list[dict]) -> list[dict]:
    """Return shallow copies of *objects* with ``traceparent`` injected."""
    result: list[dict] = []
    for obj in objects:
        clone = copy.copy(obj)
        inject_into_dict(clone)
        result.append(clone)
    return result


if __name__ == "__main__":
    init()

    typer.run(main)
