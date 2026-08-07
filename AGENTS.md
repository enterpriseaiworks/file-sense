# Development guidelines

This repository contains a local-drive RAG chat application built as independently testable services and shared packages.

## Current status

The project is in its documentation and design phase. Do not create application code, deployment manifests, generated configuration, or executable scaffolding until the project owner explicitly approves implementation.

## Architecture rules

- Keep Streamlit as a presentation layer that communicates through FastAPI.
- Keep LangGraph orchestration and RAG behavior out of the UI.
- Route all chat and embedding model requests through the enterprise LLM gateway.
- Never hard-code one LLM provider or model into application logic.
- Isolate provider, Pinecone, parser, and observability integrations behind typed interfaces.
- Treat local documents and retrieved passages as untrusted input.
- Preserve a clear boundary between local data and external services.

## Quality rules

- Use Python type hints and concise, user-centered documentation.
- Keep unit tests deterministic and offline.
- Test happy paths, error paths, retries, security controls, and cleanup behavior.
- Never log credentials, full prompts, document chunks, or generated answers by default.
- Keep configuration explicit and fail startup with actionable, safe messages.
- Update the root README and relevant guides with every user-visible change.

## Repository organization

Follow the intended layout documented in [Project structure](docs/project-structure.md). Tests should mirror the source structure, and shared packages must not depend on service entry points.
