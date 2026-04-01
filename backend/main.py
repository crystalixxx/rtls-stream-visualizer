import uvicorn

from backend.app import app
from backend.config import load_backend_config
from core.logging_config import setup_logging


def main() -> None:
    setup_logging()
    config = load_backend_config()
    uvicorn.run(app, host=config.api.host, port=config.api.port)


if __name__ == "__main__":
    main()
