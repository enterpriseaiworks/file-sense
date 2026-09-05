"""Pinecone data-plane adapter using its stable HTTP contract."""

from collections.abc import Sequence

import httpx
from desktop_agent_rag_core import Passage


class PineconeVectorStore:
    _upsert_batch_size = 100

    def __init__(self, host: str, api_key: str, namespace: str, *, timeout: float = 30) -> None:
        self._client = httpx.Client(
            base_url=host.rstrip("/"), headers={"Api-Key": api_key}, timeout=timeout
        )
        self._namespace = namespace

    def upsert(self, passages: Sequence[Passage], vectors: Sequence[Sequence[float]]) -> None:
        payload = [
            {
                "id": passage.passage_id,
                "values": list(vector),
                "metadata": {
                    "document_id": passage.document_id,
                    "source": passage.source,
                    "text": passage.text,
                    "position": passage.position,
                },
            }
            for passage, vector in zip(passages, vectors, strict=True)
        ]
        for offset in range(0, len(payload), self._upsert_batch_size):
            response = self._client.post(
                "/vectors/upsert",
                json={
                    "vectors": payload[offset : offset + self._upsert_batch_size],
                    "namespace": self._namespace,
                },
            )
            response.raise_for_status()

    def query(self, vector: Sequence[float], limit: int) -> list[Passage]:
        response = self._client.post(
            "/query",
            json={
                "vector": list(vector),
                "topK": limit,
                "namespace": self._namespace,
                "includeMetadata": True,
            },
        )
        response.raise_for_status()
        passages = []
        for match in response.json().get("matches", []):
            metadata = match.get("metadata", {})
            passages.append(
                Passage(
                    str(match["id"]),
                    str(metadata["document_id"]),
                    str(metadata["source"]),
                    str(metadata["text"]),
                    int(metadata["position"]),
                    float(match.get("score", 0)),
                )
            )
        return passages

    def delete_document(self, document_id: str) -> None:
        response = self._client.post(
            "/vectors/delete",
            json={"filter": {"document_id": {"$eq": document_id}}, "namespace": self._namespace},
        )
        response.raise_for_status()
