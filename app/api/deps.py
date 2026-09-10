from __future__ import annotations

import os

from fastapi import Header, HTTPException

from ..config import settings


def verify_auth(authorization: str = Header(...)) -> None:
    if not settings.service_secret:
        raise HTTPException(500, "SERVICE_SECRET not configured")
    expected = f"Bearer {settings.service_secret}"
    if authorization != expected:
        raise HTTPException(401, "Invalid authorization")


def validate_upload(filename: str | None, size: int) -> None:
    # Not a FastAPI dependency: `size` is only known after the handler has read the body, so a
    # dependency would have to read the upload itself and hand the bytes back.
    if not filename:
        raise HTTPException(400, "Filename is required")

    ext = os.path.splitext(filename)[1].lower()
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            415,
            f"Unsupported file type: {ext}. Allowed: {settings.allowed_extensions}",
        )

    if size > settings.max_file_size_bytes:
        raise HTTPException(413, f"File too large. Max: {settings.max_file_size_mb}MB")
