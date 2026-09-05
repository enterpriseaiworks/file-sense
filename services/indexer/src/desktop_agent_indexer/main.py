"""One-shot incremental local-drive ingestion command."""

import argparse
import sqlite3
from pathlib import Path
from threading import Event
from typing import Protocol

from desktop_agent_configuration import get_settings
from desktop_agent_connectors import (
    GatewayClient,
    LocalDocumentLoader,
    PineconeVectorStore,
    SqlManifestStore,
)
from desktop_agent_rag_core import IngestionPipeline


class StopEvent(Protocol):
    def is_set(self) -> bool: ...
    def wait(self, timeout: float) -> bool: ...


def sync_once() -> None:
    settings = get_settings()
    loader = LocalDocumentLoader(
        settings.documents_path, max_bytes=settings.max_file_size_mb * 1024 * 1024
    )
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
    database = Path("/data/indexer-manifests.sqlite3")
    database.parent.mkdir(parents=True, exist_ok=True)
    manifests = SqlManifestStore(lambda: sqlite3.connect(database))
    result = IngestionPipeline(
        gateway,
        vectors,
        manifests,
        size=settings.chunk_size_tokens,
        overlap=settings.chunk_overlap_tokens,
        retry_attempts=settings.index_retry_attempts,
    ).sync(loader.scan())
    print(
        f"Index sync completed: indexed={result.indexed}, unchanged={result.unchanged}, "
        f"deleted={result.deleted}, chunks={result.chunks}"
        f", failed={result.failed}"
    )


def run_schedule(interval_seconds: int, stop: StopEvent) -> None:
    while not stop.is_set():
        sync_once()
        if stop.wait(interval_seconds):
            break


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize local documents to Pinecone.")
    parser.add_argument("--once", action="store_true", help="run one synchronization and exit")
    arguments = parser.parse_args()
    if arguments.once:
        sync_once()
        return
    run_schedule(get_settings().index_sync_interval_seconds, Event())
