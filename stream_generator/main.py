import logging

from core.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main():
    setup_logging()
    logger.info("Application started")

    # TODO


if __name__ == "__main__":
    main()

