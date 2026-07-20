from collections.abc import MutableMapping
from typing import Protocol

import boto3
from mypy_boto3_s3 import S3Client

from nas_core.config import Settings, get_settings


class ObjectStore(Protocol):
    """Storage contract for datasets and immutable research artifacts."""

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None: ...

    def get_bytes(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class S3ObjectStore:
    def __init__(self, settings: Settings | None = None) -> None:
        config = settings or get_settings()
        self._bucket = config.object_store_bucket
        self._client: S3Client = boto3.client(
            "s3",
            endpoint_url=config.object_store_endpoint_url,
            region_name=config.object_store_region,
            aws_access_key_id=config.object_store_access_key,
            aws_secret_access_key=config.object_store_secret_key,
            use_ssl=config.object_store_secure,
        )

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=data,
            ContentType=content_type,
        )

    def get_bytes(self, key: str) -> bytes:
        response = self._client.get_object(Bucket=self._bucket, Key=key)
        return response["Body"].read()

    def exists(self, key: str) -> bool:
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
        except self._client.exceptions.ClientError as error:
            if error.response.get("Error", {}).get("Code") in {"404", "NoSuchKey"}:
                return False
            raise
        return True


class InMemoryObjectStore:
    """Small deterministic adapter for tests; never use for production data."""

    def __init__(self) -> None:
        self._objects: MutableMapping[str, bytes] = {}

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        del content_type
        self._objects[key] = data

    def get_bytes(self, key: str) -> bytes:
        return self._objects[key]

    def exists(self, key: str) -> bool:
        return key in self._objects
