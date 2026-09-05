"""Security tests for opaque, expiring local document links."""

from pathlib import Path
from urllib.parse import parse_qs, urlparse

from desktop_agent_api.file_access import FileAccess


def _parts(url: str) -> tuple[str, int, str]:
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    return parsed.path.split("/")[-2], int(query["expires"][0]), query["token"][0]


def test_explicit_file_request_creates_opaque_download_link(tmp_path: Path) -> None:
    document = tmp_path / "private-name.txt"
    document.write_text("safe content")
    access = FileAccess(tmp_path, "test-secret", "http://localhost:8000", max_bytes=1000)

    links = access.links_for_sources([document.name])

    assert access.requested("Find the document and send me a link")
    assert len(links) == 1
    assert links[0].name == document.name
    assert document.name not in links[0].url
    file_id, expires, token = _parts(links[0].url)
    assert access.resolve_download(file_id, expires, token) == document


def test_normal_chat_does_not_request_file_links(tmp_path: Path) -> None:
    access = FileAccess(tmp_path, "test-secret", "http://localhost:8000", max_bytes=1000)

    assert not access.requested("Summarize the architecture")


def test_invalid_signature_and_traversal_are_rejected(tmp_path: Path) -> None:
    document = tmp_path / "guide.txt"
    document.write_text("safe content")
    access = FileAccess(tmp_path, "test-secret", "http://localhost:8000", max_bytes=1000)
    link = access.links_for_sources([document.name])[0]
    file_id, expires, _token = _parts(link.url)

    assert access.resolve_download(file_id, expires, "0" * 64) is None
    assert access.links_for_sources(["../guide.txt"]) == []


def test_symlinks_are_rejected(tmp_path: Path) -> None:
    target = tmp_path / "target.txt"
    target.write_text("safe content")
    link = tmp_path / "linked.txt"
    link.symlink_to(target)
    access = FileAccess(tmp_path, "test-secret", "http://localhost:8000", max_bytes=1000)

    assert access.links_for_sources([link.name]) == []
