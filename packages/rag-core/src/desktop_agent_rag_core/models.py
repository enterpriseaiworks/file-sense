"""Small immutable domain models shared by services and integrations."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Literal


@dataclass(frozen=True, slots=True)
class Document:
    document_id: str
    source: str
    text: str
    checksum: str


@dataclass(frozen=True, slots=True)
class Passage:
    passage_id: str
    document_id: str
    source: str
    text: str
    position: int
    score: float = 0.0
    metadata: dict[str, str | int | float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Citation:
    passage_id: str
    source: str
    position: int


@dataclass(frozen=True, slots=True)
class Answer:
    text: str
    citations: tuple[Citation, ...]
    model: str
    abstained: bool = False


@dataclass(frozen=True, slots=True)
class Message:
    message_id: str
    conversation_id: str
    role: Literal["user", "assistant"]
    content: str
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
