FROM python:3.12-slim
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock ./
COPY services/streamlit services/streamlit
RUN uv sync --frozen --no-dev --package filesense-streamlit
USER 65532:65532
CMD ["/app/.venv/bin/streamlit", "run", "services/streamlit/src/desktop_agent_streamlit/app.py", "--server.address=0.0.0.0"]
