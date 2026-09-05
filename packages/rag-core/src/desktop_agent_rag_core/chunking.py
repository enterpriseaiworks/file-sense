"""Deterministic text normalization and overlapping chunk creation."""

import hashlib
import re

from .models import Document, Passage


def normalize_text(text: str) -> str:
    """Normalize newlines and whitespace without interpreting document instructions."""
    return re.sub(r"[ \t]+", " ", text.replace("\r\n", "\n").replace("\r", "\n")).strip()


def chunk_document(document: Document, *, size: int, overlap: int) -> list[Passage]:
    """Split on words using deterministic IDs; size is an approximate token budget."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap smaller than size")
    words = normalize_text(document.text).split()
    if not words:
        return []
    passages: list[Passage] = []
    step = size - overlap
    for position, start in enumerate(range(0, len(words), step)):
        text = " ".join(words[start : start + size])
        if not text:
            break
        digest = hashlib.sha256(f"{document.document_id}:{position}:{text}".encode()).hexdigest()
        passages.append(Passage(digest, document.document_id, document.source, text, position))
        if start + size >= len(words):
            break
    return passages
