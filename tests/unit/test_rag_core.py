from collections.abc import Sequence

from desktop_agent_connectors import InMemoryVectorStore
from desktop_agent_rag_core import (
    Document,
    GroundedChat,
    IngestionPipeline,
    Message,
    Passage,
    chunk_document,
)


class FakeEmbedder:
    def embed(self, texts: list[str]) -> list[list[float]]:
        return [[float("alpha" in text.lower()), 1.0] for text in texts]


class FlakyEmbedder(FakeEmbedder):
    def __init__(self, failures: int) -> None:
        self.failures = failures
        self.calls = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls <= self.failures:
            raise RuntimeError("temporary failure")
        return super().embed(texts)


class FakeChat:
    def rewrite(self, *, model: str, question: str, history: Sequence[Message]) -> str:
        return question

    def complete(self, *, model: str, question: str, passages: tuple[Passage, ...]) -> str:
        return f"Grounded in {passages[0].source}"


class MemoryManifests:
    def __init__(self) -> None:
        self.items: dict[str, tuple[str, str]] = {}

    def checksums(self) -> dict[str, str]:
        return {source: item[0] for source, item in self.items.items()}

    def record(self, source: str, checksum: str, document_id: str, chunks: int) -> None:
        self.items[source] = (checksum, document_id)

    def document_id(self, source: str) -> str | None:
        item = self.items.get(source)
        return item[1] if item else None

    def remove(self, source: str) -> str | None:
        item = self.items.pop(source, None)
        return item[1] if item else None


def test_chunking_is_deterministic_and_overlapping() -> None:
    document = Document("doc", "guide.txt", "one two three four five", "sum")
    first = chunk_document(document, size=3, overlap=1)
    second = chunk_document(document, size=3, overlap=1)
    assert first == second
    assert [item.text for item in first] == ["one two three", "three four five"]


def test_incremental_sync_skips_unchanged_and_deletes_missing() -> None:
    vectors = InMemoryVectorStore()
    manifests = MemoryManifests()
    pipeline = IngestionPipeline(FakeEmbedder(), vectors, manifests, size=10, overlap=1)
    document = Document("doc", "guide.txt", "alpha facts", "sum")
    assert pipeline.sync([document]).indexed == 1
    assert pipeline.sync([document]).unchanged == 1
    assert pipeline.sync([]).deleted == 1


def test_incremental_sync_retries_without_losing_previous_manifest() -> None:
    vectors = InMemoryVectorStore()
    manifests = MemoryManifests()
    original = Document("old", "guide.txt", "alpha facts", "old-sum")
    IngestionPipeline(FakeEmbedder(), vectors, manifests, size=10, overlap=1).sync([original])
    embedder = FlakyEmbedder(failures=3)
    pipeline = IngestionPipeline(embedder, vectors, manifests, size=10, overlap=1, retry_attempts=3)
    result = pipeline.sync([Document("new", "guide.txt", "changed", "new-sum")])
    assert result.failed == 1
    assert manifests.checksums()["guide.txt"] == "old-sum"
    assert embedder.calls == 3


def test_grounded_chat_abstains_without_relevant_evidence() -> None:
    chat = GroundedChat(FakeEmbedder(), InMemoryVectorStore(), FakeChat())
    answer = chat.answer("unknown", "model-a")
    assert answer.abstained
    assert answer.citations == ()


def test_grounded_chat_returns_verified_citations() -> None:
    vectors = InMemoryVectorStore()
    passage = Passage("p1", "d1", "guide.txt", "alpha facts", 0)
    vectors.upsert([passage], [[1.0, 1.0]])
    chat = GroundedChat(FakeEmbedder(), vectors, FakeChat(), relevance_threshold=0.5)
    answer = chat.answer("alpha question", "model-a")
    assert answer.text == "Grounded in guide.txt"
    assert answer.citations[0].passage_id == "p1"
    assert not answer.abstained
