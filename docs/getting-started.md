# Getting started

This guide describes the intended installation and first-use experience. Commands that depend on application code will become available during implementation.

## What users will need

- Docker Desktop or Docker Engine with Docker Compose
- A Pinecone account, API key, and serverless index configuration
- Credentials for at least one supported chat model and one embedding model
- A local folder containing PDF, DOCX, Markdown, or TXT files
- Sufficient permission for Docker to read the selected folder

## Planned setup

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

The chat page will stream answers and display expandable citations. Each citation will include a relative filename, page or section where available, and a short supporting excerpt.

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
