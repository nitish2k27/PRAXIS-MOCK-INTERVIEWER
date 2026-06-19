"""extract_text over real (tiny, generated) PDF and DOCX fixtures via LocalStorage."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from praxis.ingestion.extract import UnsupportedFileError, extract_text
from praxis.storage import LocalStorage
from tests._fixtures import make_docx, make_pdf


async def _store(tmp_path: Path, key: str, data: bytes) -> tuple[LocalStorage, str]:
    storage = LocalStorage(base_dir=str(tmp_path / "uploads"))
    url = await storage.put(key=key, fileobj=io.BytesIO(data))
    return storage, url


async def test_extract_pdf(tmp_path: Path) -> None:
    storage, url = await _store(tmp_path, "r/sample.pdf", make_pdf("Hello Praxis PDF"))
    assert "Hello Praxis PDF" in await extract_text(url, storage)


async def test_extract_docx(tmp_path: Path) -> None:
    storage, url = await _store(tmp_path, "r/sample.docx", make_docx("Hello Praxis DOCX"))
    assert "Hello Praxis DOCX" in await extract_text(url, storage)


async def test_unsupported_extension(tmp_path: Path) -> None:
    storage, url = await _store(tmp_path, "r/sample.txt", b"just text")
    with pytest.raises(UnsupportedFileError):
        await extract_text(url, storage)
