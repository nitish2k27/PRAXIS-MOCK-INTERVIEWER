"""Storage adapter Protocol — routes depend on this, not on boto3."""

from __future__ import annotations

from typing import BinaryIO, Protocol


class StorageBackend(Protocol):
    async def put(self, *, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str: ...

    async def get_url(self, key: str) -> str: ...

    async def read(self, url: str) -> bytes:
        """Return the bytes for a previously stored object, addressed by its `file_url`."""
        ...
