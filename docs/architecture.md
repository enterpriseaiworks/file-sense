# Architecture

Your Desktop Agent separates the user interface, API, ingestion pipeline, agent workflow, model gateway, storage, and observability systems. This keeps provider credentials out of the browser and allows the Streamlit interface to be replaced later without rewriting the RAG system.

## Service topology

```text
Browser
  |
  v
Streamlit UI
  |
  v
FastAPI backend ---------------- Local application database
  |                                      |
  |                                      +-- conversations
  |                                      +-- file manifests
  |                                      +-- indexing jobs
  |
  +-- LangGraph RAG workflow -------- Pinecone
  |
  +-- Enterprise LLM gateway -------- Multiple LLM providers

Read-only local folder --> Scheduled indexer --> Pinecone

Services --> OpenTelemetry Collector --> Prometheus/Grafana/Loki
```

Only the Streamlit port should be exposed for normal local use. FastAPI, the gateway, databases, and telemetry services will communicate over private Docker networks. Grafana may be exposed on a localhost-only administrative port.

## Ingestion flow

1. The indexer scans the mounted folder at startup and on a configurable schedule.
2. It compares SHA-256 file manifests with the last completed scan.
3. Supported new or changed files are parsed and normalized.
4. A token-aware recursive splitter creates metadata-rich overlapping chunks.
5. The embedding request passes through the LLM gateway.
6. Embeddings and metadata are batch-upserted into the correct Pinecone namespace.
7. Vectors belonging to removed or replaced files are deleted safely.
8. File and job status is persisted locally and displayed in Streamlit.

Planned defaults are approximately 800 tokens per chunk and 120 tokens of overlap. These values will be configurable and validated.

## Chat flow

The LangGraph state will carry the conversation identifier, messages, standalone query, retrieved chunks, relevance result, answer, citations, model selection, and error information.

The graph will:

1. Validate the question and selected model.
2. Rewrite context-dependent follow-up questions.
3. Retrieve candidate chunks from Pinecone.
4. apply maximal marginal relevance to improve source diversity.
5. Grade whether the evidence is relevant.
6. Generate an answer constrained to that evidence.
7. Assemble verified citation metadata.
8. Stream progress, answer tokens, citations, and completion events.
9. Take an explicit abstention path when the evidence is insufficient.

Document content will be treated as untrusted data, not executable model instructions.

## Enterprise multi-LLM gateway

The gateway will expose a normalized API while supporting multiple configured providers and model aliases. It will provide:

- User-selected exact-model routing
- Automatic, cost-aware, and latency-aware routing policies
- Ordered fallback with an option to disable silent fallback
- Provider health checks, timeouts, retries, cooldowns, and circuit breakers
- Model allowlists, budgets, rate limits, concurrency controls, and token limits
- Input and output security policies
- Sanitized audit events, metrics, logs, and distributed traces
- Stable routes for chat, query rewriting, relevance grading, and embeddings

Chat models can change without rebuilding the document index. An embedding-model change requires a compatible Pinecone namespace and controlled re-indexing.

## Data ownership

| Data | Planned location |
|---|---|
| Original files | User's local folder |
| File access | Read-only indexer mount |
| Embeddings and chunk metadata | Pinecone |
| Conversations and manifests | Local application database |
| Gateway usage and audit metadata | Gateway PostgreSQL database |
| Sanitized telemetry | Local observability services |
| Provider credentials | Runtime secrets, never the browser |
