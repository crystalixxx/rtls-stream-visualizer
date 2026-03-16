from fastapi import FastAPI

from backend.api.health import router as health_router
from backend.config import BackendConfig, load_backend_config


def create_app(config: BackendConfig | None = None) -> FastAPI:
    app = FastAPI()
    app.state.config = config or load_backend_config()
    app.include_router(health_router)

    return app


app = create_app()
