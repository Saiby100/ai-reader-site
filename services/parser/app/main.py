import asyncio
import json
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, File, HTTPException, Header, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from .config import settings
from .models import CapabilitiesResponse, ParseResponse, ProgressEvent
from .parser import is_model_loaded, load_models, parse_document

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    load_models()
    yield


app = FastAPI(title="Document Parser", lifespan=lifespan)


def verify_auth(authorization: str = Header(...)) -> None:
    if not settings.service_secret:
        raise HTTPException(500, "SERVICE_SECRET not configured")
    expected = f"Bearer {settings.service_secret}"
    if authorization != expected:
        raise HTTPException(401, "Invalid authorization")


def _validate_file(filename: str | None, size: int) -> None:
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


@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "model_loaded": is_model_loaded()}


@app.get("/capabilities")
async def capabilities() -> CapabilitiesResponse:
    return CapabilitiesResponse(
        allowed_extensions=sorted(settings.allowed_extensions_set),
        max_file_size_mb=settings.max_file_size_mb,
    )


@app.post("/parse", dependencies=[Depends(verify_auth)])
async def parse(file: UploadFile = File(...)) -> ParseResponse:
    content = await file.read()
    _validate_file(file.filename, len(content))

    try:
        result = await asyncio.to_thread(parse_document, content, file.filename or "document")
    except Exception as exc:
        logger.exception("Parse failed for %s", file.filename)
        raise HTTPException(500, f"Parse failed: {exc}") from exc

    return result


@app.post("/parse/stream", dependencies=[Depends(verify_auth)])
async def parse_stream(file: UploadFile = File(...)) -> StreamingResponse:
    content = await file.read()
    _validate_file(file.filename, len(content))

    async def event_generator() -> AsyncGenerator[str, None]:
        yield _sse_event(ProgressEvent(stage="started", progress=0.0, message="Upload received"))
        yield _sse_event(ProgressEvent(stage="parsing", progress=0.1, message="Parsing document..."))

        try:
            result = await asyncio.to_thread(parse_document, content, file.filename or "document")
            yield _sse_event(ProgressEvent(stage="completed", progress=1.0, message="Parse complete"))
            yield f"event: result\ndata: {result.model_dump_json()}\n\n"
        except Exception as exc:
            logger.exception("Stream parse failed for %s", file.filename)
            yield _sse_event(ProgressEvent(stage="failed", progress=0.0, message=str(exc)))

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_event(event: ProgressEvent) -> str:
    return f"event: progress\ndata: {json.dumps(event.model_dump())}\n\n"


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )
