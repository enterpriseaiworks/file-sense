FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY packages/configuration packages/configuration
COPY packages/connectors packages/connectors
COPY packages/rag-core packages/rag-core
COPY services/api services/api
RUN uv sync --frozen --no-dev --package filesense-api
USER 65532:65532
CMD ["/app/.venv/bin/uvicorn", "desktop_agent_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
