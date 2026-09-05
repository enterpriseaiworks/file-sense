# Implementation roadmap

> <span style="color: green;">**Green = implemented at the currently approved foundation level.**</span>

## <span style="color: green;">Phase 0: design and documentation — ✅ implemented</span>

<span style="color: green;">**Status: implemented at foundation level; approved and recorded.**</span> See [Implementation decisions](decisions.md). Provider selection, authentication, retention, and evaluation thresholds remain deferred until their dependent phases.

- Define product behavior, architecture, stack, data boundaries, and acceptance criteria.
- Establish user, contributor, architecture, and security documentation.
- Obtain explicit approval before writing application code.

## <span style="color: green;">Phase 1: runnable foundation — ✅ implemented</span>

<span style="color: green;">**Status: implemented at foundation level.**</span> The Python workspace, health API, Streamlit status shell, quality tooling, and Docker service definitions exist. Full dependency readiness checks and persistence arrive in the next approved phase.

- Create the Docker Compose topology, configuration validation, health checks, FastAPI service, Streamlit shell, gateway, and databases.
- Provide a verified quick-start path and clear setup diagnostics.

## <span style="color: green;">Phase 2: ingestion and retrieval — ✅ core workflow implemented</span>

<span style="color: green;">**Status: core workflow implemented.**</span> The indexer safely scans PDF, DOCX, Markdown, plain text, reStructuredText, CSV, and JSON files; normalizes and chunks them with deterministic identifiers; requests embeddings through the gateway; reconciles additions/changes/deletions with a durable manifest; and uses Pinecone behind a typed adapter. It supports scheduled or one-shot synchronization and bounded per-document retry while preserving the last good manifest on failure. Detailed operator status remains an extension.

- Implement supported loaders, normalization, token-aware chunking, deterministic identifiers, embeddings, Pinecone storage, and incremental scheduled synchronization.
- Add document status, retry behavior, and deletion reconciliation.

## <span style="color: green;">Phase 3: grounded chat — ✅ core workflow implemented</span>

<span style="color: green;">**Status: core workflow implemented.**</span> A compiled LangGraph workflow rewrites conversation-aware follow-ups, retrieves and relevance-gates evidence, diversifies sources, routes explicitly between generation and abstention, and returns verified citations. PostgreSQL persists conversations and messages. FastAPI emits SSE answer/citation events and the Streamlit UI renders them. Persistent LangGraph checkpoints remain an extension.

- Implement the LangGraph workflow, retrieval grading, MMR selection, abstention, streaming, conversation persistence, model selection, and citations.

## Phase 4: enterprise gateway controls

**Status: partially implemented.** All embedding and chat traffic uses configurable aliases through LiteLLM. The gateway has sanitized logging, bounded retries, failure cooldowns, and provider-neutral application interfaces. FastAPI requires a constant-time checked API key, and PostgreSQL stores metadata-only success/failure audit events. Budgets, per-user distributed rate limits, advanced guardrails, and capability reporting remain.

- Add multi-provider routing, exact-model mode, fallback policies, budgets, rate limits, guardrails, audit events, and model capability reporting.

## Phase 5: quality and operations

**Status: partially implemented.** Deterministic offline tests cover loaders, chunking, incremental synchronization, retry cleanup, abstention, citations, streaming, settings validation, API liveness, and a small groundedness acceptance dataset. Ruff, strict mypy, and GitHub Actions CI are configured. Expanded evaluations, dashboards, security integration tests, and full end-to-end infrastructure tests remain.

- Add evaluation datasets, retrieval and groundedness measurements, dashboards, security tests, end-to-end tests, CI, and finalized operational documentation.
