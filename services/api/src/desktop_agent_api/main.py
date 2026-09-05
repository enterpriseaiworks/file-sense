"""FastAPI boundary for health, model discovery, and grounded chat."""

import json
import secrets
from collections.abc import AsyncIterator
from contextlib import suppress
from functools import lru_cache
from typing import Annotated

import anyio
from desktop_agent_configuration import Settings, get_settings
from desktop_agent_connectors import (
    GatewayClient,
    PineconeVectorStore,
    PostgresConversationStore,
)
from desktop_agent_rag_core import GroundedChat
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from .file_access import FileAccess

app = FastAPI(title="FileSense API", version="0.2.0")


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=16_000)
    model: str = Field(min_length=1, max_length=200)
    conversation_id: str | None = Field(default=None, min_length=1, max_length=100)


class CitationResponse(BaseModel):
    passage_id: str
    source: str
    position: int


class FileLinkResponse(BaseModel):
    name: str
    url: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[CitationResponse]
    model: str
    abstained: bool
    conversation_id: str
    files: list[FileLinkResponse] = Field(default_factory=list)


class ConversationResponse(BaseModel):
    conversation_id: str
    model: str


@lru_cache(maxsize=1)
def build_chat() -> GroundedChat:
    settings = get_settings()
    gateway = GatewayClient(
        str(settings.llm_gateway_url),
        settings.llm_gateway_api_key.get_secret_value(),
        settings.embedding_model_alias,
        embedding_provider_model=settings.embedding_provider_model,
        chat_provider_model=settings.chat_provider_model,
    )
    vectors = PineconeVectorStore(
        str(settings.pinecone_host),
        settings.pinecone_api_key.get_secret_value(),
        settings.pinecone_namespace,
    )
    return GroundedChat(
        gateway,
        vectors,
        gateway,
        candidate_count=settings.retrieval_candidate_count,
        final_count=settings.retrieval_final_count,
        relevance_threshold=settings.relevance_threshold,
    )


@lru_cache(maxsize=1)
def build_conversations() -> PostgresConversationStore:
    settings = get_settings()
    store = PostgresConversationStore(settings.database_url.get_secret_value())
    store.initialize()
    return store


@lru_cache(maxsize=1)
def build_file_access() -> FileAccess:
    settings = get_settings()
    return FileAccess(
        settings.documents_path,
        settings.app_api_key.get_secret_value(),
        str(settings.public_api_base_url),
        max_bytes=settings.max_file_size_mb * 1024 * 1024,
    )


def settings_dependency() -> Settings:
    try:
        return get_settings()
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="Runtime configuration is incomplete."
        ) from error


def authorize(
    settings: Annotated[Settings, Depends(settings_dependency)],
    x_api_key: Annotated[str | None, Header()] = None,
) -> None:
    expected = settings.app_api_key.get_secret_value()
    if not x_api_key or not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=401, detail="A valid API key is required.")


@app.get("/health/live", tags=["health"])
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", tags=["health"])
async def readiness() -> dict[str, str]:
    try:
        get_settings()
    except Exception:
        return {"status": "configuration_required"}
    return {"status": "ready"}


@app.get("/v1/models", tags=["chat"])
async def models(
    settings: Annotated[Settings, Depends(settings_dependency)],
    _authorized: Annotated[None, Depends(authorize)],
) -> dict[str, list[str]]:
    return {"models": list(settings.chat_model_aliases)}


@app.get("/v1/files/{file_id}/download", tags=["files"])
async def download_file(
    file_id: str,
    expires: Annotated[int, Query(gt=0)],
    token: Annotated[str, Query(min_length=64, max_length=64)],
) -> FileResponse:
    path = build_file_access().resolve_download(file_id, expires, token)
    if path is None:
        raise HTTPException(status_code=404, detail="The file link is invalid or expired.")
    with suppress(Exception):
        build_conversations().record_audit(
            "file.downloaded", conversation_id=None, model=None, outcome="success"
        )
    return FileResponse(path, filename=path.name)


@app.post("/v1/conversations", response_model=ConversationResponse, tags=["chat"])
async def create_conversation(
    model: str,
    settings: Annotated[Settings, Depends(settings_dependency)],
    _authorized: Annotated[None, Depends(authorize)],
) -> ConversationResponse:
    if model not in settings.chat_model_aliases:
        raise HTTPException(status_code=422, detail="The selected model is not allowed.")
    try:
        conversation_id = build_conversations().create(model)
    except Exception as error:
        raise HTTPException(
            status_code=503, detail="Conversation storage is unavailable."
        ) from error
    return ConversationResponse(conversation_id=conversation_id, model=model)


@app.post("/v1/chat", response_model=ChatResponse, tags=["chat"])
async def chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(settings_dependency)],
    _authorized: Annotated[None, Depends(authorize)],
) -> ChatResponse:
    return await anyio.to_thread.run_sync(process_chat, request, settings)


def process_chat(request: ChatRequest, settings: Settings) -> ChatResponse:
    """Execute blocking provider/database work outside the API event loop."""
    if request.model not in settings.chat_model_aliases:
        raise HTTPException(status_code=422, detail="The selected model is not allowed.")
    conversations: PostgresConversationStore | None = None
    conversation_id = request.conversation_id
    try:
        conversations = build_conversations()
        conversation_id = request.conversation_id or conversations.create(request.model)
        history = conversations.history(conversation_id)
        result = build_chat().answer(request.question, request.model, history)
        conversations.add_message(conversation_id, "user", request.question)
        conversations.add_message(conversation_id, "assistant", result.text)
        conversations.record_audit(
            "chat.completed",
            conversation_id=conversation_id,
            model=request.model,
            outcome="abstained" if result.abstained else "answered",
        )
    except Exception as error:
        if conversations is not None:
            with suppress(Exception):
                conversations.record_audit(
                    "chat.failed",
                    conversation_id=conversation_id,
                    model=request.model,
                    outcome=type(error).__name__,
                )
        raise HTTPException(
            status_code=502, detail="A configured retrieval dependency failed."
        ) from error
    citations = [
        CitationResponse(passage_id=item.passage_id, source=item.source, position=item.position)
        for item in result.citations
    ]
    file_links = (
        build_file_access().links_for_sources(item.source for item in citations)
        if build_file_access().requested(request.question)
        else []
    )
    return ChatResponse(
        answer=result.text,
        citations=citations,
        model=result.model,
        abstained=result.abstained,
        conversation_id=conversation_id,
        files=[FileLinkResponse(name=item.name, url=item.url) for item in file_links],
    )


@app.post("/v1/chat/stream", tags=["chat"])
async def stream_chat(
    request: ChatRequest,
    settings: Annotated[Settings, Depends(settings_dependency)],
    _authorized: Annotated[None, Depends(authorize)],
) -> StreamingResponse:
    async def events() -> AsyncIterator[str]:
        yield _sse("status", {"stage": "retrieving"})
        try:
            response = await anyio.to_thread.run_sync(process_chat, request, settings)
        except HTTPException as error:
            yield _sse("error", {"detail": error.detail})
            return
        for token in response.answer.split(" "):
            yield _sse("token", {"text": f"{token} "})
        yield _sse(
            "citations",
            {"items": [item.model_dump() for item in response.citations]},
        )
        if response.files:
            yield _sse("files", {"items": [item.model_dump() for item in response.files]})
        yield _sse(
            "done",
            {
                "conversation_id": response.conversation_id,
                "model": response.model,
                "abstained": response.abstained,
            },
        )

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def _sse(event: str, data: object) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"
