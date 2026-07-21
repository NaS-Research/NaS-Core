from collections.abc import MutableMapping
from pathlib import Path, PurePosixPath
from typing import Protocol

import boto3
from mypy_boto3_s3 import S3Client

from nas_core.config import Settings, get_settings
from nas_core.storage.layout import DataLayout


class ObjectStore(Protocol):
    """Storage contract for datasets and immutable research artifacts."""

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None: ...

    def get_bytes(self, key: str) -> bytes: ...

    def exists(self, key: str) -> bool: ...


class FileSystemObjectStore:
    """Local object-store adapter constrained to a validated NaS data root."""

    def __init__(self, data_root: Path) -> None:
        layout = DataLayout(data_root)
        layout.validate()
        self._root = (layout.root / "object-store").resolve()

    def put_bytes(self, key: str, data: bytes, *, content_type: str) -> None:
        del content_type
        path = self._path_for(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as destination:
            destination.write(data)

    def get_bytes(self, key: str) -> bytes:
        return self._path_for(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self._path_for(key).is_file()

    def _path_for(self, key: str) -> Path:
        object_key = PurePosixPath(key)
        if (
            not key
            or object_key.is_absolute()
            or "\\" in key
            or any(part in {"", ".", ".."} for part in object_key.parts)
        ):
            raise ValueError("object key must be a safe relative POSIX path")
        path = (self._root / Path(*object_key.parts)).resolve()
        if self._root not in path.parents:
            raise ValueError("object key escapes the configured object-store root")
        return path


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


def get_object_store(settings: Settings | None = None) -> ObjectStore:
    """Build the configured replaceable object-store adapter."""

    config = settings or get_settings()
    if config.object_store_backend == "filesystem":
        return FileSystemObjectStore(config.data_root)
    return S3ObjectStore(config)
