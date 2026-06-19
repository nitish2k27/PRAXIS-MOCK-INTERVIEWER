"""Extract plain text from a stored resume/JD file (PDF or DOCX).

Bytes are read through the storage adapter (never the filesystem directly), and the
blocking pdfplumber/docx2txt work runs in an executor so the event loop is never blocked.
"""

from __future__ import annotations

import asyncio
import io

from praxis.storage import StorageBackend


class UnsupportedFileError(ValueError):
    """Raised when a file_url has no supported (.pdf/.docx) extension."""


async def extract_text(file_url: str, storage: StorageBackend) -> str:
    """Read the stored object and return its extracted plain text."""
    suffix = _suffix(file_url)
    data = await storage.read(file_url)
    if suffix == "pdf":
        return await asyncio.to_thread(_pdf_to_text, data)
    if suffix == "docx":
        return await asyncio.to_thread(_docx_to_text, data)
    raise UnsupportedFileError(f"unsupported file type for {file_url!r}")


def _suffix(file_url: str) -> str:
    return file_url.rsplit(".", 1)[-1].lower() if "." in file_url else ""


def _pdf_to_text(data: bytes) -> str:
    import pdfplumber

    parts: list[str] = []
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def _docx_to_text(data: bytes) -> str:
    import docx2txt

    return (docx2txt.process(io.BytesIO(data)) or "").strip()
