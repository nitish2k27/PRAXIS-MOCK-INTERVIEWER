"""Local-disk storage backend for dev + tests."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import BinaryIO

from praxis.config import settings


class LocalStorage:
    def __init__(self, base_dir: str | None = None) -> None:
        self.base = Path(base_dir or settings.storage_local_dir)
        self.base.mkdir(parents=True, exist_ok=True)

    async def put(self, *, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str:
        path = self.base / key
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(_write, path, fileobj)
        return f"file://{path.resolve().as_posix()}"

    async def get_url(self, key: str) -> str:
        return f"file://{(self.base / key).resolve().as_posix()}"

    async def read(self, url: str) -> bytes:
        path = Path(url[len("file://") :] if url.startswith("file://") else url)
        return await asyncio.to_thread(path.read_bytes)


def _write(path: Path, fileobj: BinaryIO) -> None:
    with path.open("wb") as out:
        while True:
            chunk = fileobj.read(64 * 1024)
            if not chunk:
                break
            out.write(chunk)
