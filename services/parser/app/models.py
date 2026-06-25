from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

ElementType = Literal[
    "title",
    "heading",
    "paragraph",
    "list_item",
    "table",
    "image",
    "code",
    "formula",
    "caption",
]


class DocumentElement(BaseModel):
    """A single node in the parsed document tree.

    Shared metadata (``ref``/``page``/``label``/``charspan``) is present on every
    element; the remaining fields are payload that only applies to certain types.
    """

    # --- shared metadata (every element) ---
    type: ElementType
    """Discriminator for the element kind."""
    ref: str | None = None
    """Docling self_ref JSON-pointer (e.g. '#/texts/12') — stable anchor for citations,
    click-to-source, and highlighting."""
    page: int | None = None
    """1-based source page the element originated from, when known."""
    label: str | None = None
    """Raw docling DocItemLabel, preserved so distinctions the renderer collapses
    (caption vs footnote vs body) remain queryable."""
    charspan: tuple[int, int] | None = None
    """Character span [start, end] within the element's source text, for precise
    sub-element highlighting / citation ranges."""
    alignment: Literal["center", "right"] | None = None
    """Horizontal text alignment inferred from the source geometry; ``None`` means the
    default (left). Only set for PDFs, where bounding boxes are available."""

    # --- per-type payload ---
    level: int | None = None
    """Heading depth (1-6) for 'heading' elements."""
    text: str | None = None
    """Plain text content for text-bearing elements; LaTeX source for 'formula'."""
    language: str | None = None
    """Detected source language for 'code' elements."""
    html: str | None = None
    """Pre-rendered HTML for 'table' elements."""
    data_uri: str | None = None
    """Inline data URI for 'image' elements."""
    children: list[DocumentElement] = []
    """Nested child elements, e.g. items under a list."""


class ParseConfidence(BaseModel):
    """Docling's quality assessment of the parse."""

    grade: str
    """Overall quality grade: poor / fair / good / excellent / unspecified."""
    score: float | None = None
    """Mean confidence score in [0, 1], when available."""


class ParseMetadata(BaseModel):
    """Metadata about the parse operation."""

    filename: str
    """Original uploaded filename."""
    page_count: int
    """Number of pages in the source document."""
    format_detected: str
    """File format inferred from the extension."""
    parse_duration_ms: int
    """Wall-clock parse time in milliseconds."""
    status: str
    """Docling ConversionStatus: success / partial_success / failure / skipped."""
    confidence: ParseConfidence | None = None
    """Docling confidence report, when available."""
    binary_hash: str | None = None
    """Content hash of the source file — usable as a cache / dedup key."""


class ParseResponse(BaseModel):
    """Top-level response from the /parse endpoint."""

    document: list[DocumentElement]
    """Ordered, render-ready document tree."""
    metadata: ParseMetadata
    """Document-level metadata about the parse."""
    errors: list[str] = []
    """Human-readable parse errors (component failures), when any."""


class CapabilitiesResponse(BaseModel):
    """Server-defined parsing capabilities advertised to clients."""

    allowed_extensions: list[str]
    max_file_size_mb: int
