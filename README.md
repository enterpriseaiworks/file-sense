<div align="center">

# Your filse sense agent

### Ask questions across your local documents with grounded answers and citations.

</div>

Your Desktop Agent is a planned, self-hosted chat application that turns an explicitly selected folder on your computer into a searchable knowledge base. It will use retrieval-augmented generation (RAG) to find relevant passages, give those passages to a selected large language model (LLM), and return a streamed answer with citations to the original files.

> [!IMPORTANT]
> This repository is currently in the **documentation and design phase**. The application code and Docker services have not been implemented yet.

## What it will do

- Read PDF, DOCX, Markdown, and plain-text files from a read-only local folder.
- Split documents into meaningful, overlapping chunks and generate embeddings.
- Store embeddings and document metadata in Pinecone.
- Detect new, changed, and deleted files during scheduled synchronization.
- Retrieve the most relevant source passages for each question.
- Use LangGraph to rewrite follow-up questions, retrieve evidence, grade relevance, and generate grounded answers.
- Stream answers through a Streamlit chat interface.
- Show citations with the source filename, page or section, and supporting excerpt.
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
Grounded answer with source citations
```

RAG helps an LLM answer from the user's documents rather than relying only on information learned during model training. If the retrieved documents do not contain enough evidence, the agent will say so instead of inventing an answer.

## Planned quick start

The completed application will use one Docker Compose command to start the local stack:

```bash
docker compose up --build
```

Before startup, users will copy the example environment file, add provider credentials, and set the local document directory:

```bash
cp .env.example .env
```

The exact commands will become active after implementation. See the [getting-started guide](docs/getting-started.md) for the planned installation experience.

## Application components

- **Streamlit UI** — chat, model selection, citations, document status, and usage views.
- **FastAPI** — stable API boundary for chat, conversations, indexing, health, and gateway status.
- **LangChain** — document loaders, splitters, embedding adapters, and retrieval building blocks.
- **LangGraph** — controllable and testable RAG workflow orchestration.
- **Pinecone** — managed vector storage and similarity search.
- **Enterprise LLM gateway** — multi-provider routing, fallback, policy enforcement, budgets, security, and telemetry.
- **Indexer** — scheduled incremental synchronization of the mounted document folder.
- **PostgreSQL/SQLite** — gateway operational data and local application state.
- **OpenTelemetry, Prometheus, Grafana, and Loki** — traces, metrics, dashboards, and sanitized logs.

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

The approved product direction and documentation foundation are complete. Implementation remains intentionally paused until the implementation plan is explicitly approved.

## Acknowledgements

This project is designed to use the open-source [LangChain](https://github.com/langchain-ai/langchain) and [LangGraph](https://github.com/langchain-ai/langgraph) ecosystems. Its repository documentation and organization take inspiration from LangChain's clear separation of core concepts, integrations, tests, and contributor guidance. No LangChain source code has been copied into this repository.
