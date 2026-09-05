"""PostgreSQL-backed durable conversation and message storage."""

from collections.abc import Callable
from datetime import datetime
from typing import Literal, cast
from uuid import uuid4

import psycopg
from desktop_agent_rag_core import Message


class PostgresConversationStore:
    """Persist chat history without logging or storing retrieval context."""

    def __init__(
        self,
        database_url: str,
        connect: Callable[..., psycopg.Connection] = psycopg.connect,
    ) -> None:
        self._database_url = database_url.replace("postgresql+psycopg://", "postgresql://", 1)
        self._connect = connect

    def initialize(self) -> None:
        with self._connect(self._database_url) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS conversations (
                    conversation_id TEXT PRIMARY KEY,
                    model TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS messages (
                    message_id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL
                        REFERENCES conversations(conversation_id) ON DELETE CASCADE,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS messages_conversation_created "
                "ON messages(conversation_id, created_at)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    conversation_id TEXT,
                    model TEXT,
                    outcome TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def create(self, model: str) -> str:
        conversation_id = str(uuid4())
        with self._connect(self._database_url) as connection:
            connection.execute(
                "INSERT INTO conversations(conversation_id, model) VALUES (%s, %s)",
                (conversation_id, model),
            )
        return conversation_id

    def add_message(self, conversation_id: str, role: str, content: str) -> Message:
        if role not in {"user", "assistant"}:
            raise ValueError("message role must be user or assistant")
        message_id = str(uuid4())
        with self._connect(self._database_url) as connection:
            row = connection.execute(
                """
                INSERT INTO messages(message_id, conversation_id, role, content)
                VALUES (%s, %s, %s, %s)
                RETURNING created_at
                """,
                (message_id, conversation_id, role, content),
            ).fetchone()
        if row is None:
            raise RuntimeError("message insert did not return a timestamp")
        safe_role = cast(Literal["user", "assistant"], role)
        return Message(message_id, conversation_id, safe_role, content, cast(datetime, row[0]))

    def history(self, conversation_id: str, limit: int = 20) -> list[Message]:
        with self._connect(self._database_url) as connection:
            rows = connection.execute(
                """
                SELECT message_id, role, content, created_at
                FROM messages WHERE conversation_id = %s
                ORDER BY created_at DESC LIMIT %s
                """,
                (conversation_id, limit),
            ).fetchall()
        return [
            Message(
                str(row[0]),
                conversation_id,
                cast(Literal["user", "assistant"], row[1]),
                str(row[2]),
                cast(datetime, row[3]),
            )
            for row in reversed(rows)
        ]

    def record_audit(
        self,
        event_type: str,
        *,
        conversation_id: str | None,
        model: str | None,
        outcome: str,
    ) -> None:
        """Record metadata only; prompts, passages, and answers are intentionally excluded."""
        with self._connect(self._database_url) as connection:
            connection.execute(
                """
                INSERT INTO audit_events(
                    event_id, event_type, conversation_id, model, outcome
                ) VALUES (%s, %s, %s, %s, %s)
                """,
                (str(uuid4()), event_type, conversation_id, model, outcome),
            )
