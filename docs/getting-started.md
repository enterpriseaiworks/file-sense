# Getting started

This guide covers the implemented text-document indexing and grounded chat path.

## Foundation setup

The development workspace requires `uv` and a Python 3.12 interpreter. `uv` honors the repository's `.python-version` file.

```bash
make sync
make check
```

The checks run Ruff, strict mypy, and offline pytest tests. To prepare container configuration:

```bash
cp .env.example .env
```

Replace every `change-me` value and set `DOCUMENTS_PATH` to a folder Docker may mount read-only. The current base stack is started with:

```bash
docker compose up --build
```

The base stack serves the chat application. Run an incremental document sync separately:

- Streamlit UI: `http://localhost:8501`
- FastAPI backend: `http://localhost:8000`
- FastAPI documentation: `http://localhost:8000/docs`

The backend binds only to `127.0.0.1`; protected endpoints still require the configured
`APP_API_KEY` in the `X-API-Key` request header.

Run an incremental document sync separately:

```bash
docker compose --profile ingestion run --rm indexer --once
```

The indexer supports PDF, DOCX, UTF-8 Markdown, plain text, reStructuredText, CSV, and JSON. Optional telemetry services use the `observability` Compose profile.

## Optional LangSmith tracing

LangGraph tracing can be sent to LangSmith by creating an API key at
[smith.langchain.com](https://smith.langchain.com), setting `LANGSMITH_API_KEY` in `.env`,
and changing `LANGSMITH_TRACING` to `true`. Traces use the `filesense` project.
Inputs and outputs are hidden by default so questions, retrieved document text, answers, vectors,
and source filenames are not sent in trace payloads. Operational metadata remains enabled so
LangSmith can associate token counts with provider/model pricing. Recreate the API container after
changing these values:

```bash
docker compose up -d --force-recreate api
```

## What users will need

- Docker Desktop or Docker Engine with Docker Compose
- A Pinecone account, API key, and serverless index configuration
- Credentials for at least one supported chat model and one embedding model
- A local folder containing PDF, DOCX, Markdown, or TXT files
- Sufficient permission for Docker to read the selected folder

## Planned complete-product setup

1. Download or clone this repository.
2. Copy `.env.example` to `.env`.
3. Set `DOCUMENTS_PATH` to the folder the application may read.
4. Add Pinecone credentials.
5. Configure one or more LLM providers in the gateway configuration.
6. Start the application with Docker Compose.
7. Open the Streamlit URL shown by Docker.
8. Confirm that the setup screen reports healthy services.
9. Wait for the startup scan or select **Sync now**.
10. Choose an available chat model and ask a question.

## Expected first-use experience

The setup page will explain missing configuration in plain language. It will show separate status indicators for the mounted folder, Pinecone, embedding route, chat models, indexer, and FastAPI service.

After synchronization, the document page will show:

- Number of discovered and indexed files
- Last successful synchronization time
- Added, changed, removed, skipped, and failed file counts
- Per-file processing errors with safe remediation guidance

The chat page streams answer text only. Citation metadata remains internal for grounding and auditing; document filenames are not displayed in the UI.

When a user explicitly asks to find, open, download, or receive a link to a document, the chat
displays **Open &lt;filename&gt;** buttons using the exact filename from the configured folder. These
use opaque, signed URLs that expire after five minutes. The API never places an absolute path or
source filename in the URL; filenames appear only after an explicit file request.

## Local folder behavior

A web browser cannot silently read arbitrary host folders. The user will explicitly configure a folder before Docker starts. It will be mounted read-only at a fixed path inside the indexer container.

Changing the folder will require updating `.env` and restarting the stack. The application will never expose the absolute host path in chat citations or public APIs.

## Stopping the application

The completed project will document normal shutdown and data-preserving restart commands. Removing application volumes or Pinecone vectors will be a separate, explicit reset operation with a confirmation step.

## Troubleshooting topics planned for v1

- Docker cannot access the selected folder
- Pinecone authentication or index-dimension mismatch
- Provider credentials are missing or invalid
- A selected model is unavailable
- A document is unsupported, encrypted, empty, or corrupt
- Indexing stops after a partial provider failure
- Retrieval returns no relevant evidence
- Citations do not include page numbers for a format that lacks pages
