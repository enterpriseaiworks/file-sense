"""Durable manifest metadata using a DB-API connection factory."""

from collections.abc import Callable
from typing import Any, Protocol


class Connection(Protocol):
    def execute(self, sql: str, parameters: tuple[object, ...] = ()) -> Any: ...
    def commit(self) -> None: ...
    def close(self) -> None: ...


class SqlManifestStore:
    """Store only file identity/status metadata, never document contents."""

    def __init__(self, connect: Callable[[], Connection]) -> None:
        self._connect = connect
        connection = connect()
        try:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS document_manifests ("
                "source TEXT PRIMARY KEY, checksum TEXT NOT NULL, "
                "document_id TEXT NOT NULL, chunks INTEGER NOT NULL)"
            )
            connection.commit()
        finally:
            connection.close()

    def checksums(self) -> dict[str, str]:
        connection = self._connect()
        try:
            return {
                str(row[0]): str(row[1])
                for row in connection.execute("SELECT source, checksum FROM document_manifests")
            }
        finally:
            connection.close()

    def record(self, source: str, checksum: str, document_id: str, chunks: int) -> None:
        connection = self._connect()
        try:
            connection.execute("DELETE FROM document_manifests WHERE source = ?", (source,))
            connection.execute(
                "INSERT INTO document_manifests(source, checksum, document_id, chunks) "
                "VALUES (?, ?, ?, ?)",
                (source, checksum, document_id, chunks),
            )
            connection.commit()
        finally:
            connection.close()

    def document_id(self, source: str) -> str | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT document_id FROM document_manifests WHERE source = ?", (source,)
            ).fetchone()
            return str(row[0]) if row else None
        finally:
            connection.close()

    def remove(self, source: str) -> str | None:
        connection = self._connect()
        try:
            row = connection.execute(
                "SELECT document_id FROM document_manifests WHERE source = ?", (source,)
            ).fetchone()
            connection.execute("DELETE FROM document_manifests WHERE source = ?", (source,))
            connection.commit()
            return str(row[0]) if row else None
        finally:
            connection.close()
