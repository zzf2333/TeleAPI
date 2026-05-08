FROM node:24-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim AS runtime
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-editable

COPY src/ src/
COPY config.example.yaml config.example.yaml
COPY --from=frontend-builder /app/frontend/dist frontend/dist

RUN mkdir -p /app/data

EXPOSE 8080
VOLUME /app/data

CMD ["uv", "run", "--no-dev", "uvicorn", "teleapi.main:app", "--host", "0.0.0.0", "--port", "8080"]
