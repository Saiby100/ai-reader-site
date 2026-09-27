from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from ...models import ParseResponse
from ...parsing import parse_document
from ..deps import validate_upload, verify_auth

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/parse", dependencies=[Depends(verify_auth)])
async def parse(file: UploadFile = File(...)) -> ParseResponse:
    content = await file.read()
    validate_upload(file.filename, len(content))

    try:
        result = await asyncio.to_thread(parse_document, content, file.filename or "document")
    except Exception as exc:
        logger.exception("Parse failed for %s", file.filename)
        raise HTTPException(500, f"Parse failed: {exc}") from exc

    return result
