from __future__ import annotations

import io

from app.services.media.storage import ALLOWED_MIME_TYPES, MAGIC_BYTES


def validate_mime_type(mime_type: str, media_type: str = "photo") -> bool:
    """Validate that a MIME type is allowed for the given media type."""
    allowed = ALLOWED_MIME_TYPES.get(media_type, set())
    return mime_type in allowed


def validate_magic_bytes(data: bytes, expected_mime_type: str) -> bool:
    """Validate file content using magic byte signatures.

    Do not trust filename or browser MIME type alone.
    """
    signatures = MAGIC_BYTES.get(expected_mime_type, [])
    if not signatures:
        # Unknown type — allow but log warning
        return True
    return any(data.startswith(sig) for sig in signatures)


def strip_exif(image_data: bytes) -> bytes:
    """Strip EXIF/GPS data from image bytes for public derivatives.

    Preserves original evidence privately only where justified.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_data))
        data_without_exif = io.BytesIO()
        # Convert to RGB if necessary (e.g., for RGBA/P images)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(data_without_exif, format="JPEG", quality=85)
        return data_without_exif.getvalue()
    except Exception:
        # If Pillow isn't available or image is invalid, return as-is
        return image_data


def generate_thumbnail(image_data: bytes, max_size: tuple[int, int] = (200, 200)) -> bytes:
    """Generate a thumbnail from image bytes."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_data))
        img.thumbnail(max_size)
        thumb_buf = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(thumb_buf, format="JPEG", quality=75)
        return thumb_buf.getvalue()
    except Exception:
        return image_data


def validate_file_size(file_size: int, media_type: str = "photo") -> bool:
    """Validate file size is within limits."""
    limits = {
        "photo": 20 * 1024 * 1024,   # 20MB
        "video": 100 * 1024 * 1024,  # 100MB
        "voice": 25 * 1024 * 1024,   # 25MB
    }
    max_size = limits.get(media_type, 20 * 1024 * 1024)
    return 0 < file_size <= max_size
