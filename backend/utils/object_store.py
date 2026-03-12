from __future__ import annotations

import os
import uuid
from dataclasses import dataclass

import boto3

from utils.integrations import object_store_provider


@dataclass
class StoredObject:
    provider: str
    key: str
    size_bytes: int | None = None
    mime_type: str | None = None


def _local_base_dir(app_instance_path: str) -> str:
    base = os.path.join(app_instance_path, "uploads")
    os.makedirs(base, exist_ok=True)
    return base


def put_bytes(*, app_instance_path: str, content: bytes, filename: str | None = None) -> StoredObject:
    provider = object_store_provider()
    filename = filename or "file"
    ext = ""
    if "." in filename:
        ext = "." + filename.split(".")[-1][:12]

    key = f"{uuid.uuid4().hex}{ext}"

    if provider == "local":
        base = _local_base_dir(app_instance_path)
        path = os.path.join(base, key)
        with open(path, "wb") as f:
            f.write(content)
        return StoredObject(provider="local", key=key, size_bytes=len(content))

    if provider in ("s3", "minio"):
        endpoint = os.getenv("OBJECT_STORE_ENDPOINT") or None
        region = os.getenv("OBJECT_STORE_REGION") or None
        bucket = os.getenv("OBJECT_STORE_BUCKET") or ""
        access = os.getenv("OBJECT_STORE_ACCESS_KEY") or ""
        secret = os.getenv("OBJECT_STORE_SECRET_KEY") or ""
        if not bucket or not access or not secret:
            raise RuntimeError("Object store not configured (bucket/access/secret missing)")

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
        )
        client.put_object(Bucket=bucket, Key=key, Body=content)
        return StoredObject(provider=provider, key=key, size_bytes=len(content))

    raise RuntimeError(f"Unsupported OBJECT_STORE_PROVIDER: {provider}")


def get_local_path(*, app_instance_path: str, key: str) -> str:
    base = _local_base_dir(app_instance_path)
    return os.path.join(base, key)


def presign_get_url(*, key: str, expires_seconds: int = 300) -> str | None:
    """
    Returns a presigned GET URL for S3/MinIO providers.
    For local storage, returns None (use send_file).
    """
    provider = object_store_provider()
    if provider == "local":
        return None

    if provider in ("s3", "minio"):
        endpoint = os.getenv("OBJECT_STORE_ENDPOINT") or None
        region = os.getenv("OBJECT_STORE_REGION") or None
        bucket = os.getenv("OBJECT_STORE_BUCKET") or ""
        access = os.getenv("OBJECT_STORE_ACCESS_KEY") or ""
        secret = os.getenv("OBJECT_STORE_SECRET_KEY") or ""
        if not bucket or not access or not secret:
            raise RuntimeError("Object store not configured (bucket/access/secret missing)")

        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            region_name=region,
            aws_access_key_id=access,
            aws_secret_access_key=secret,
        )
        return client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=int(expires_seconds),
        )

    raise RuntimeError(f"Unsupported OBJECT_STORE_PROVIDER: {provider}")

