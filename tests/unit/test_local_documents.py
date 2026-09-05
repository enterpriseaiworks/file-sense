from pathlib import Path

from desktop_agent_connectors import LocalDocumentLoader


def test_loader_skips_symlinks_and_oversized_files(tmp_path: Path) -> None:
    (tmp_path / "ok.txt").write_text("safe", encoding="utf-8")
    (tmp_path / "large.txt").write_text("too large", encoding="utf-8")
    (tmp_path / "link.txt").symlink_to(tmp_path / "ok.txt")
    documents = LocalDocumentLoader(tmp_path, max_bytes=5).scan()
    assert [document.source for document in documents] == ["ok.txt"]


def test_loader_skips_invalid_utf8(tmp_path: Path) -> None:
    (tmp_path / "bad.txt").write_bytes(b"\xff")
    assert LocalDocumentLoader(tmp_path, max_bytes=10).scan() == []
