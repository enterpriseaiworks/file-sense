"""Incremental ingestion use case independent of parsers and vector providers."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from .chunking import chunk_document
from .models import Document, Passage
from .ports import Embedder, VectorStore


class ManifestStore(Protocol):
    def checksums(self) -> dict[str, str]: ...
    def document_id(self, source: str) -> str | None: ...
    def record(self, source: str, checksum: str, document_id: str, chunks: int) -> None: ...
    def remove(self, source: str) -> str | None: ...


@dataclass(frozen=True, slots=True)
class SyncResult:
    indexed: int = 0
    unchanged: int = 0
    deleted: int = 0
    chunks: int = 0
    failed: int = 0


class IngestionPipeline:
    def __init__(
        self,
        embedder: Embedder,
        vectors: VectorStore,
        manifests: ManifestStore,
        *,
        size: int,
        overlap: int,
        retry_attempts: int = 3,
    ) -> None:
        self._embedder = embedder
        self._vectors = vectors
        self._manifests = manifests
        self._size = size
        self._overlap = overlap
        self._retry_attempts = retry_attempts

    def sync(self, documents: Iterable[Document]) -> SyncResult:
        previous = self._manifests.checksums()
        current: set[str] = set()
        indexed = unchanged = deleted = chunks = failed = 0
        for document in documents:
            current.add(document.source)
            if previous.get(document.source) == document.checksum:
                unchanged += 1
                continue
            old_id = self._manifests.document_id(document.source)
            passages = chunk_document(document, size=self._size, overlap=self._overlap)
            try:
                self._index_with_retries(passages)
            except Exception:
                failed += 1
                continue
            if old_id:
                self._vectors.delete_document(old_id)
            self._manifests.record(
                document.source, document.checksum, document.document_id, len(passages)
            )
            indexed += 1
            chunks += len(passages)
        for source in previous.keys() - current:
            document_id = self._manifests.remove(source)
            if document_id:
                self._vectors.delete_document(document_id)
                deleted += 1
        return SyncResult(indexed, unchanged, deleted, chunks, failed)

    def _index_with_retries(self, passages: Sequence[Passage]) -> None:
        for attempt in range(self._retry_attempts):
            try:
                if passages:
                    vectors = self._embedder.embed([item.text for item in passages])
                    self._vectors.upsert(passages, vectors)
                return
            except Exception:
                if attempt + 1 == self._retry_attempts:
                    raise
