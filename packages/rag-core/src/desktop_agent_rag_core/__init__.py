"""Provider-neutral retrieval augmented generation primitives."""

from .chunking import chunk_document, normalize_text
from .ingestion import IngestionPipeline, ManifestStore, SyncResult
from .models import Answer, Citation, Document, Message, Passage
from .ports import ChatModel, ConversationStore, Embedder, VectorStore
from .workflow import GroundedChat

__all__ = [
    "Answer",
    "ChatModel",
    "Citation",
    "ConversationStore",
    "Document",
    "Embedder",
    "GroundedChat",
    "IngestionPipeline",
    "ManifestStore",
    "Message",
    "Passage",
    "SyncResult",
    "VectorStore",
    "chunk_document",
    "normalize_text",
]
