"""Secure, filename-private access to explicitly requested local documents."""

import hashlib
import hmac
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlencode

from desktop_agent_connectors import LocalDocumentLoader

_FILE_INTENT = re.compile(
    r"\b(find|locate|open|download)\b.*\b(file|document|pdf|docx|link)\b|"
    r"\b(send|give|share)\b.*\blink\b",
    re.IGNORECASE,
)


@dataclass(frozen=True, slots=True)
class FileLink:
    name: str
    url: str


class FileAccess:
    """Create and validate opaque, short-lived document download links."""

    def __init__(
        self,
        root: Path,
        secret: str,
        public_api_base_url: str,
        *,
        max_bytes: int,
        link_ttl_seconds: int = 300,
    ) -> None:
        self._root = root.resolve()
        self._secret = secret.encode()
        self._public_api_base_url = public_api_base_url.rstrip("/")
        self._max_bytes = max_bytes
        self._link_ttl_seconds = link_ttl_seconds

    @staticmethod
    def requested(question: str) -> bool:
        """Require explicit file/link intent so normal chat never exposes links."""
        return bool(_FILE_INTENT.search(question))

    def links_for_sources(self, sources: Iterable[str], *, limit: int = 5) -> list[FileLink]:
        links: list[FileLink] = []
        seen: set[str] = set()
        for source in sources:
            if source in seen:
                continue
            seen.add(source)
            path = self._safe_source(source)
            if path is None:
                continue
            file_id = self._file_id(source)
            expires = int(time.time()) + self._link_ttl_seconds
            token = self._signature(file_id, expires)
            query = urlencode({"expires": expires, "token": token})
            links.append(
                FileLink(
                    name=path.name,
                    url=f"{self._public_api_base_url}/v1/files/{file_id}/download?{query}",
                )
            )
            if len(links) == limit:
                break
        return links

    def resolve_download(self, file_id: str, expires: int, token: str) -> Path | None:
        """Return a safe file only when the opaque ID and expiring signature are valid."""
        if expires < int(time.time()) or not hmac.compare_digest(
            token, self._signature(file_id, expires)
        ):
            return None
        for path in self._iter_files():
            source = path.relative_to(self._root).as_posix()
            if hmac.compare_digest(file_id, self._file_id(source)):
                return path
        return None

    def _file_id(self, source: str) -> str:
        return hmac.new(self._secret, f"file-id:{source}".encode(), hashlib.sha256).hexdigest()[:32]

    def _signature(self, file_id: str, expires: int) -> str:
        message = f"download:{file_id}:{expires}".encode()
        return hmac.new(self._secret, message, hashlib.sha256).hexdigest()

    def _iter_files(self) -> Iterable[Path]:
        if not self._root.is_dir():
            return
        for path in self._root.rglob("*"):
            if path.is_file() and path.suffix.lower() in LocalDocumentLoader.supported_suffixes:
                source = path.relative_to(self._root).as_posix()
                safe = self._safe_source(source)
                if safe is not None:
                    yield safe

    def _safe_source(self, source: str) -> Path | None:
        relative = Path(source)
        if relative.is_absolute() or ".." in relative.parts:
            return None
        candidate = self._root / relative
        current = self._root
        for part in relative.parts:
            current /= part
            if current.is_symlink():
                return None
        if not candidate.is_file():
            return None
        resolved = candidate.resolve()
        if not resolved.is_relative_to(self._root):
            return None
        if resolved.suffix.lower() not in LocalDocumentLoader.supported_suffixes:
            return None
        try:
            if resolved.stat().st_size > self._max_bytes:
                return None
        except OSError:
            return None
        return resolved
