from __future__ import annotations

import logging
import math
import os
import tempfile
import time

from docling.datamodel.document import ConversionResult

from ..config import settings
from ..models import ParseConfidence, ParseMetadata, ParseResponse
from .converter import get_converter
from .ligatures import repair_lossy_ligatures
from .links import extract_pdf_links
from .tree import build_tree, enum_value

logger = logging.getLogger(__name__)


def parse_document(file_bytes: bytes, filename: str) -> ParseResponse:
    converter = get_converter()
    ext = os.path.splitext(filename)[1].lower()
    start = time.perf_counter()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        result = converter.convert(tmp_path)
        links = extract_pdf_links(file_bytes) if ext == ".pdf" else {}
        elements = build_tree(result, links)
        errors = [e.error_message for e in result.errors]

        if ext == ".pdf" and settings.ocr_fallback:
            elements = repair_lossy_ligatures(file_bytes, tmp_path, elements, errors, links)

        duration_ms = int((time.perf_counter() - start) * 1000)
        return ParseResponse(
            document=elements,
            metadata=_build_metadata(result, filename, ext, duration_ms),
            errors=errors,
        )
    except Exception:
        logger.exception("Failed to parse %s", filename)
        raise
    finally:
        os.unlink(tmp_path)


def _build_metadata(
    result: ConversionResult, filename: str, ext: str, duration_ms: int
) -> ParseMetadata:
    doc = result.document
    page_count = doc.num_pages() if hasattr(doc, "num_pages") else 0

    origin = getattr(doc, "origin", None)
    binary_hash = getattr(origin, "binary_hash", None)

    return ParseMetadata(
        filename=filename,
        page_count=page_count,
        format_detected=ext.lstrip("."),
        parse_duration_ms=duration_ms,
        status=enum_value(result.status) or "unknown",
        confidence=_extract_confidence(result),
        binary_hash=str(binary_hash) if binary_hash is not None else None,
    )


def _extract_confidence(result: ConversionResult) -> ParseConfidence | None:
    report = getattr(result, "confidence", None)
    if report is None:
        return None

    grade = enum_value(getattr(report, "mean_grade", None))
    if grade is None:
        return None

    score = getattr(report, "mean_score", None)
    if score is None or (isinstance(score, float) and math.isnan(score)):
        score = None
    else:
        score = float(score)

    return ParseConfidence(grade=grade, score=score)
