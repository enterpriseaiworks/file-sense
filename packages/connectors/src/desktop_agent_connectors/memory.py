"""Deterministic vector adapter used by offline tests and local development."""

import math
from collections.abc import Sequence
from dataclasses import replace

from desktop_agent_rag_core import Passage


class InMemoryVectorStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[Passage, tuple[float, ...]]] = {}

    def upsert(self, passages: Sequence[Passage], vectors: Sequence[Sequence[float]]) -> None:
        if len(passages) != len(vectors):
            raise ValueError("passages and vectors must have the same length")
        for passage, vector in zip(passages, vectors, strict=True):
            self._items[passage.passage_id] = (passage, tuple(vector))

    def query(self, vector: Sequence[float], limit: int) -> list[Passage]:
        ranked = [
            replace(item, score=self._cosine(vector, stored))
            for item, stored in self._items.values()
        ]
        return sorted(ranked, key=lambda item: item.score, reverse=True)[:limit]

    def delete_document(self, document_id: str) -> None:
        self._items = {
            key: value for key, value in self._items.items() if value[0].document_id != document_id
        }

    @staticmethod
    def _cosine(left: Sequence[float], right: Sequence[float]) -> float:
        if len(left) != len(right):
            return -1.0
        denominator = math.sqrt(sum(x * x for x in left)) * math.sqrt(sum(x * x for x in right))
        return (
            sum(x * y for x, y in zip(left, right, strict=True)) / denominator
            if denominator
            else 0.0
        )
