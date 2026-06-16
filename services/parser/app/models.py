from __future__ import annotations

from pydantic import BaseModel


class BoundingBox(BaseModel):
    """Spatial position of an element on a page."""

    x: float
    y: float
    width: float
    height: float
    page: int


class DocumentElement(BaseModel):
    """A single node in the parsed document tree."""

    type: str
    level: int | None = None
    text: str | None = None
    html: str | None = None
    data_uri: str | None = None
    bbox: BoundingBox | None = None
    page: int | None = None
    children: list[DocumentElement] = []


class ParseMetadata(BaseModel):
    """Metadata about the parse operation."""

    filename: str
    page_count: int
    format_detected: str
    parse_duration_ms: int


class ParseResponse(BaseModel):
    """Top-level response from the /parse endpoint."""

    document: list[DocumentElement]
    metadata: ParseMetadata
    errors: list[str] = []


class CapabilitiesResponse(BaseModel):
    """Server-defined parsing capabilities advertised to clients."""

    allowed_extensions: list[str]
    max_file_size_mb: int
