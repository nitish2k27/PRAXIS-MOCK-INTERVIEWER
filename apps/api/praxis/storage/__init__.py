"""Storage adapter package. `get_storage()` returns the configured backend."""

from __future__ import annotations

from .base import StorageBackend
from .local import LocalStorage

__all__ = ["StorageBackend", "LocalStorage", "get_storage"]

_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """FastAPI dependency. Tests override via `app.dependency_overrides`."""
    global _storage
    if _storage is None:
        from praxis.config import settings

        if settings.storage_backend == "s3":
            from .s3 import S3Storage

            _storage = S3Storage()
        else:
            _storage = LocalStorage()
    return _storage
