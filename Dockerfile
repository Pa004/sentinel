FROM python:3.12-slim AS builder

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

FROM python:3.12-slim

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
# Runtime needs /app/src + /app/backend (editable install link) + packaging
# metadata. Heavy dirs (.venv, tests, frontend/node_modules) are excluded
# via .dockerignore. Note: Fly allows 50 connections but the app caps at
# 3 concurrent analyses (429 beyond that) — tune MAX_CONCURRENT_ANALYSES first.
COPY --from=builder /app/src /app/src
COPY --from=builder /app/backend /app/backend
COPY --from=builder /app/pyproject.toml /app/pyproject.toml
COPY --from=builder /app/README.md /app/README.md

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
