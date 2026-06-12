FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq5 gettext && \
    rm -rf /var/lib/apt/lists/*

RUN pip install uv==0.10.* --no-cache-dir

WORKDIR /app
COPY . .

RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH"
