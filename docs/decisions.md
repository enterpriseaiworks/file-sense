# Implementation decisions

This record distinguishes approved Phase 0–2 choices from decisions that remain open for later phases.

## Approved foundation

| Concern | Decision | Reason |
|---|---|---|
| Runtime | Python 3.12 | Current typed async ecosystem with a stable deployment target |
| Workspace | `uv` | Reproducible Python and dependency management across services |
| RAG components | LangChain | Loaders, splitting, messages, prompts, and retrieval primitives |
| Agent orchestration | LangGraph `StateGraph` | Explicit nodes, conditional routing, streaming, and durable checkpoints |
| API | FastAPI with Server-Sent Events planned for chat | Typed contracts and one-way streaming without WebSocket complexity |
| UI | Streamlit | Presentation layer communicating only through FastAPI |
| Durable state | PostgreSQL 16 | Conversations, checkpoints, manifests, jobs, settings, and audits |
| Temporary state | Redis 7 | Expiring cache, sessions, rate limits, and distributed locks |
| Vector store | Pinecone | Versioned document embeddings and metadata |
| Inbound gateway | Caddy | Small local reverse-proxy configuration and request-size enforcement |
| LLM gateway | LiteLLM Proxy behind project-owned interfaces | Multi-provider normalized chat and embedding routes |
| Local runtime | Docker Compose | Reproducible local service topology |
| Quality | Ruff, mypy, pytest | Formatting, linting, strict typing, and offline deterministic tests |

LangChain and LangGraph will be added when their Phase 3/5 functionality begins; foundation packages do not import them prematurely.

## Security defaults

- Only Streamlit is exposed for ordinary local use.
- Grafana is optional and bound to localhost.
- Backend services use an internal Docker network.
- The source folder is mounted read-only into the indexer only.
- Raw messages, prompts, answers, and document chunks are not logged by default.
- Model routes are empty until approved aliases and credentials are configured.

## Deferred decisions

The owner must approve these before their dependent phase starts:

- Initial chat and embedding providers, aliases, and embedding dimension
- Single-user versus authenticated multi-user v1
- Exact file-count, total-folder-size, and processing-time limits
- Pinecone cloud, region, index, and namespace lifecycle
- Retrieval thresholds and evaluation targets
- Retention periods for conversations, audits, and indexing history
- Production secret-management and deployment platform
