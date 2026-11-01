from __future__ import annotations

import hashlib
import os
import uuid
from pathlib import Path

from app.core.config import get_settings

settings = get_settings()

# Allowed MIME types per media type
ALLOWED_MIME_TYPES: dict[str, set[str]] = {
    "photo": {"image/jpeg", "image/png", "image/webp", "image/heic"},
    "video": {"video/mp4", "video/webm", "video/quicktime"},
    "voice": {"audio/webm", "audio/mp4", "audio/mpeg", "audio/wav", "audio/ogg"},
}

# Magic byte signatures for validation
MAGIC_BYTES: dict[str, list[bytes]] = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/webp": [b"RIFF"],
    "image/heic": [b"\x00\x00\x00\x1cftypheic"],
    "video/mp4": [b"\x00\x00\x00\x1cftypmp41", b"\x00\x00\x00\x1cftypmp42", b"\x00\x00\x00\x20ftypisom"],
    "video/webm": [b"\x1aE\xdf\xa3"],
    "audio/webm": [b"\x1aE\xdf\xa3"],
    "audio/mp4": [b"\x00\x00\x00\x1cftypM4A "],
    "audio/mpeg": [b"\xff\xfb", b"\xff\xf3", b"\xff\xf2", b"ID3"],
    "audio/wav": [b"RIFF"],
    "audio/ogg": [b"OggS"],
}

# Local storage fallback directory
LOCAL_MEDIA_DIR = Path("data/media")


def get_s3_key_prefix(report_id: uuid.UUID, media_type: str) -> str:
    """Generate the S3 key prefix for a media asset."""
    return f"reports/{report_id}/{media_type}"


def generate_presigned_upload(s3_key: str, mime_type: str, expires_in: int = 3600) -> tuple[str, int]:
    """Generate a presigned S3 upload URL.

    When S3 is not configured (local dev), returns a local file:// URL
    and creates the local directory structure.
    """
    if not settings.S3_MEDIA_BUCKET:
        # Local fallback: store files on disk
        local_path = LOCAL_MEDIA_DIR / s3_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_url = f"file://{local_path}"
        return local_url, expires_in

    try:
        import boto3
        from botocore.config import Config as BotoConfig

        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            config=BotoConfig(signature_version="s3v4"),
        )
        url = s3_client.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": settings.S3_MEDIA_BUCKET,
                "Key": s3_key,
                "ContentType": mime_type,
            },
            ExpiresIn=expires_in,
        )
        return url, expires_in
    except Exception:
        # Fallback to local if boto3 not available
        local_path = LOCAL_MEDIA_DIR / s3_key
        local_path.parent.mkdir(parents=True, exist_ok=True)
        return f"file://{local_path}", expires_in


def generate_presigned_download(s3_key: str, expires_in: int = 3600) -> str | None:
    """Generate a presigned S3 download URL for media access."""
    if not settings.S3_MEDIA_BUCKET:
        local_path = LOCAL_MEDIA_DIR / s3_key
        if local_path.exists():
            return f"file://{local_path}"
        return None

    try:
        import boto3
        from botocore.config import Config as BotoConfig

        s3_client = boto3.client(
            "s3",
            region_name=settings.AWS_REGION,
            endpoint_url=settings.AWS_ENDPOINT_URL or None,
            config=BotoConfig(signature_version="s3v4"),
        )
        url = s3_client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_MEDIA_BUCKET, "Key": s3_key},
            ExpiresIn=expires_in,
        )
        return url
    except Exception:
        return None


def compute_sha256(data: bytes) -> str:
    """Compute the SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()
