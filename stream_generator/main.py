import logging
import typer

from pathlib import Path

from core.logging_config import setup_logging
from core.config import load_config, get_config
from core.validate import Validator
from core.udp.client import UdpClient

logger = logging.getLogger(__name__)


def init():
    setup_logging()
    load_config()
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
    validator = Validator(config.validation.schema_path)
    objects, errors = validator.get_validated_objects_from_file(source)

    if errors:
        logger.error("Validation errors: %s", errors)

    with UdpClient(ip, port) as udp_client:
        udp_client.send(objects, batch_size, time_between_batches)

    logger.info("Stream generated successfully")


if __name__ == "__main__":
    init()

    typer.run(main)
