.PHONY: sync format lint typecheck test check

sync:
	UV_CACHE_DIR=/private/tmp/filesense-uv-cache uv sync --all-packages

format:
	UV_CACHE_DIR=/private/tmp/filesense-uv-cache uv run ruff format .

lint:
	UV_CACHE_DIR=/private/tmp/filesense-uv-cache uv run ruff check .

typecheck:
	UV_CACHE_DIR=/private/tmp/filesense-uv-cache uv run mypy packages/configuration/src packages/rag-core/src packages/connectors/src services/api/src services/indexer/src

test:
	UV_CACHE_DIR=/private/tmp/filesense-uv-cache uv run pytest -m "not integration and not e2e"

check: lint typecheck test
