FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 gettext && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv==0.10.* --no-cache-dir

WORKDIR /app

COPY pyproject.toml uv.lock ./
ARG MODE=locale
RUN if [ "$MODE" = "debug" ]; then uv sync --frozen; else uv sync --frozen --no-dev; fi
ENV PATH="/app/.venv/bin:$PATH"

COPY . .
