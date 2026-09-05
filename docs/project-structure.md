# Project structure

The repository will follow a service-oriented layout inspired by LangChain's separation of implementation, integrations, tests, documentation, and development guidance.

```text
filesense/
|-- README.md
|-- AGENTS.md
|-- CONTRIBUTING.md
|-- SECURITY.md
|-- docs/
|   |-- architecture.md
|   |-- getting-started.md
|   |-- project-structure.md
|   |-- roadmap.md
|   `-- security.md
|-- services/
|   |-- api/                  # FastAPI and LangGraph application
|   |-- indexer/              # Scheduled local-drive ingestion
|   |-- streamlit/            # User-facing chat application
|   `-- gateway/              # Multi-LLM gateway configuration
|-- packages/                 # Shared Python packages, added by implementation phase
|   |-- rag-core/             # Chunking, retrieval, citations, graph state
|   |-- connectors/           # Pinecone and document integrations
|   `-- observability/        # Logging, metrics, tracing, redaction
|-- tests/
|   |-- unit/
|   |-- integration/
|   |-- e2e/
|   `-- evaluation/
|-- deploy/
|   |-- docker/
|   `-- observability/
`-- .github/
    |-- ISSUE_TEMPLATE/
    `-- workflows/
```

Directories marked as future implementation will not be populated with application code until the implementation plan is approved.

Phases 0–2 are approved. The current implementation contains service entry points for the API, indexer, and Streamlit shell plus the shared configuration package. Remaining shared packages will be introduced only when their corresponding behavior is implemented.

## Layer responsibilities

- **Services** contain independently runnable processes and their narrow entry points.
- **Shared packages** hold reusable, typed application logic without UI or deployment concerns.
- **Integrations** isolate Pinecone, model-gateway, and document-loader dependencies.
- **Tests** mirror the production layers and keep network-free unit tests separate from provider integrations.
- **Deploy** contains Docker and observability configuration.
- **Docs** explains the product for users, operators, contributors, and security reviewers.

## Dependency direction

The UI may depend on the FastAPI contract but not on RAG implementation internals. Services may use shared packages. Shared RAG logic may depend on defined integration interfaces, while provider-specific integrations implement those interfaces. Provider SDK details must not leak into the Streamlit UI or public API models.
