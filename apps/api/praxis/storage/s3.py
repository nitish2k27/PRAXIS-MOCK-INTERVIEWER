"""S3 / R2 storage backend (boto3). Imported lazily so dev doesn't require boto3 at import time."""

from __future__ import annotations

import asyncio
from typing import Any, BinaryIO

import boto3

from praxis.config import settings


class S3Storage:
    def __init__(self) -> None:
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url,
            region_name=settings.s3_region,
            aws_access_key_id=settings.s3_access_key_id,
            aws_secret_access_key=settings.s3_secret_access_key,
        )
        self._bucket = settings.s3_bucket
        self._public_base = settings.s3_public_base_url

    async def put(self, *, key: str, fileobj: BinaryIO, content_type: str | None = None) -> str:
        extra: dict[str, Any] = {"ContentType": content_type} if content_type else {}
        await asyncio.to_thread(
            self._client.upload_fileobj, fileobj, self._bucket, key, ExtraArgs=extra
        )
        return await self.get_url(key)

    async def get_url(self, key: str) -> str:
        if self._public_base:
            return f"{self._public_base.rstrip('/')}/{key}"
        return f"s3://{self._bucket}/{key}"

    async def read(self, url: str) -> bytes:
        key = self._key_from_url(url)
        obj = await asyncio.to_thread(self._client.get_object, Bucket=self._bucket, Key=key)
        body: bytes = await asyncio.to_thread(obj["Body"].read)
        return body

    def _key_from_url(self, url: str) -> str:
        if url.startswith("s3://"):
            # s3://bucket/key... → drop scheme + bucket segment.
            return url[len("s3://") :].split("/", 1)[1]
        if self._public_base and url.startswith(self._public_base):
            return url[len(self._public_base.rstrip("/")) + 1 :]
        raise ValueError(f"cannot derive S3 key from url: {url}")
