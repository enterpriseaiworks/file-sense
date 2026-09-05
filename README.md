<div align="center">

# FileSense

### Ask questions across your local documents with grounded answers.

</div>

FileSense is a self-hosted chat application that turns an explicitly selected folder on your computer into a searchable knowledge base. It uses retrieval-augmented generation (RAG) to find relevant passages, give those passages to a selected large language model (LLM), and return a grounded answer. Citation metadata remains internal and filenames are not displayed in chat.

The Streamlit interface uses a project-local bot avatar for its visible branding and browser-tab icon. Its responsive, centered chat layout includes a compact model picker, distinct user messages, assistant avatars, and a persistent rounded composer labeled “Message your FileSense agent.”

Explicit requests to find, open, or download a document return its exact folder filename with a
short-lived link. The URL itself contains an opaque ID rather than a filename or host path and
expires after five minutes.

> [!IMPORTANT]
> The core ingestion, Pinecone retrieval, relevance-gated chat, abstention, model selection, and citation path is implemented. See the [roadmap](docs/roadmap.md) for production extensions that remain.

## System architecture

![FileSense system architecture](docs/assets/system-architecture-v3.png)

The primary request path is Streamlit UI → API Gateway → FastAPI Agent Service → RAG Application → LLM API Gateway → selected LLM. PostgreSQL preserves durable application memory, Redis accelerates temporary state, and Pinecone remains the document vector store.

For local development, Streamlit is available on `127.0.0.1:8501` and FastAPI is available on
`127.0.0.1:8000`. The FastAPI documentation is served at `http://localhost:8000/docs`; protected
endpoints require the configured application API key.

## What it will do

- Read PDF, DOCX, Markdown, and plain-text files from a read-only local folder.
- Split documents into meaningful, overlapping chunks and generate embeddings.
- Store embeddings and document metadata in Pinecone.
- Detect new, changed, and deleted files during scheduled synchronization.
- Retrieve the most relevant source passages for each question.
- Use LangGraph to rewrite follow-up questions, retrieve evidence, grade relevance, and generate grounded answers.
- Stream answers through a Streamlit chat interface.
- Keep citation metadata internal without displaying document filenames in chat.
- Let users choose among multiple approved LLMs instead of being locked to one provider.
- Route model requests through a secure, observable enterprise LLM gateway.
- Preserve local conversation and indexing history.

## How RAG works in this project

```text
Local documents
      |
      v
Parse and normalize
      |
      v
Token-aware chunking
      |
      v
Embedding model -> Pinecone vector index
                         |
User question            |
      |                  |
      v                  v
LangGraph query workflow and retrieval
      |
      v
Enterprise multi-LLM gateway
      |
      v
Grounded answer text
```

RAG helps an LLM answer from the user's documents rather than relying only on information learned during model training. If the retrieved documents do not contain enough evidence, the agent will say so instead of inventing an answer.

## Foundation development

Install the locked Python workspace and run its offline checks with:

```bash
make sync
make check
```

To inspect the local stack configuration, first create local configuration:

```bash
cp .env.example .env
```

Replace every `change-me` value and set `DOCUMENTS_PATH`. Start the chat stack with `docker compose up --build`, then run an incremental index sync with `docker compose --profile ingestion run --rm indexer --once`. Use `docker compose --profile ingestion up --build` to keep scheduled synchronization running.

## Application components

- **Streamlit UI** — chat and model selection with answer-only output.
- **API gateway** — protects, validates, limits, and routes incoming requests to FastAPI.
- **FastAPI** — stable API boundary for chat, conversations, indexing, health, and gateway status.
- **LangChain** — document loaders, splitters, embedding adapters, and retrieval building blocks.
- **LangGraph** — controllable and testable RAG workflow orchestration.
- **Pinecone** — managed vector storage and similarity search.
- **Enterprise LLM gateway** — multi-provider routing, fallback, policy enforcement, budgets, security, and telemetry.
- **Indexer** — scheduled incremental synchronization of the mounted document folder.
- **PostgreSQL** — durable conversations, LangGraph checkpoints, settings, indexing records, and audit metadata.
- **Redis** — expiring sessions, retrieval cache, rate-limit counters, and distributed job locks.
- **OpenTelemetry, Prometheus, Grafana, and Loki** — traces, metrics, dashboards, and sanitized logs.
- **LangSmith (optional)** — privacy-preserving LangGraph and LLM traces with token and cost metadata when explicitly enabled.

Read the [architecture guide](docs/architecture.md) for the complete request and ingestion flows.

## Multi-LLM support

The application will not require one LLM vendor. The gateway will support configurable providers such as OpenAI, Azure OpenAI, Anthropic, Google Gemini or Vertex AI, AWS Bedrock, Ollama, and compatible APIs.

Users will be able to select an approved model for a conversation or choose an automatic routing policy. Administrators will be able to add provider and model configuration without changing the RAG application code.

Embedding models require stricter handling than chat models: each Pinecone index or namespace must stay associated with a compatible embedding model and vector dimension. Changing that model will require a controlled re-index of the documents.

## Local and cloud data boundaries

The application services will run locally in Docker. The selected document folder will be mounted read-only into the indexing service.

Pinecone and hosted model providers are external services. Document chunks and questions may therefore leave the local computer. Raw prompts and document text will not be stored in application logs by default. A local model such as Ollama can reduce model-provider exposure, but Pinecone remains external in the planned v1 architecture.

Review the [security and privacy guide](docs/security.md) before using confidential documents.

## Documentation

- [Getting started](docs/getting-started.md)
- [Architecture](docs/architecture.md)
- [Project structure](docs/project-structure.md)
- [Security and privacy](docs/security.md)
- [Implementation roadmap](docs/roadmap.md)
- [Contributing](CONTRIBUTING.md)

## Project status

The core vertical path is implemented: PDF, DOCX, and text document ingestion; deterministic chunking; bounded embedding and vector-upsert batches for large documents; Pinecone reconciliation and retrieval; a compiled LangGraph relevance/generation/abstention workflow; grounded answers; internal citations; FastAPI; and Streamlit chat. The roadmap identifies remaining production extensions.

## Acknowledgements

This project is designed to use the open-source [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph) ecosystems. Its repository documentation and organization take inspiration from LangChain's clear separation of core concepts, integrations, tests, and contributor guidance. No LangChain source code has been copied into this repository.
