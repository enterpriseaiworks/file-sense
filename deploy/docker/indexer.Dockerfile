FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY packages/configuration packages/configuration
COPY packages/connectors packages/connectors
COPY packages/rag-core packages/rag-core
COPY services/indexer services/indexer
RUN uv sync --frozen --no-dev --package filesense-indexer
RUN mkdir -p /data && chown 65532:65532 /data
USER 65532:65532
ENTRYPOINT ["/app/.venv/bin/filesense-indexer"]
