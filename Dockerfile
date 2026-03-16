FROM python:3.12-slim

ENV POETRY_VERSION=2.2.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

COPY pyproject.toml poetry.lock README.md ./
COPY backend ./backend
COPY core ./core
COPY config ./config
COPY migrations ./migrations
COPY stream_generator ./stream_generator
COPY stream_handler ./stream_handler
COPY udp_receiver ./udp_receiver

RUN poetry install --only main

EXPOSE ${API_PORT:-8000}

CMD ["python", "-m", "backend.main"]
