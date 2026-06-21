import base64
import logging
import math
import os
import tempfile
import time

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from .config import settings
from .models import DocumentElement, ParseConfidence, ParseMetadata, ParseResponse

logger = logging.getLogger(__name__)

_converter: DocumentConverter | None = None


def _make_converter() -> DocumentConverter:
    """Build the single Docling converter used for all documents.

    Tuned for ordinary ebooks (text + images): image extraction is on (cheap) so
    figures survive, while OCR and formula/code enrichment default off because they
    are CPU-heavy and unnecessary for born-digital documents. Enrichment runs a
    vision-language model per equation/code block and can peg a CPU machine, so it is
    opt-in via ``settings.enable_enrichment`` for capable (ideally GPU) hardware.
    """
    options = PdfPipelineOptions()
    options.do_formula_enrichment = settings.enable_enrichment
    options.do_code_enrichment = settings.enable_enrichment
    options.do_ocr = settings.do_ocr
    options.generate_picture_images = settings.generate_picture_images
    options.images_scale = settings.images_scale
    options.accelerator_options = AcceleratorOptions(
        device=settings.accelerator_device,
        num_threads=settings.num_threads,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def load_models() -> None:
    global _converter
    logger.info(
        "Loading Docling models (enrichment=%s, ocr=%s, device=%s)...",
        settings.enable_enrichment,
        settings.do_ocr,
        settings.accelerator_device,
    )
    _converter = _make_converter()
    # Force model loading now (construction is lazy) so the first request isn't slowed
    # by model initialization.
    _converter.initialize_pipeline(InputFormat.PDF)
    logger.info("Docling models loaded")


def is_model_loaded() -> bool:
    return _converter is not None


_FORMAT_BY_EXT: dict[str, InputFormat] = {
    ".pdf": InputFormat.PDF,
    ".docx": InputFormat.DOCX,
    ".pptx": InputFormat.PPTX,
    ".html": InputFormat.HTML,
    ".htm": InputFormat.HTML,
    ".md": InputFormat.MD,
    ".txt": InputFormat.MD,
}


def parse_document(file_bytes: bytes, filename: str) -> ParseResponse:
    if _converter is None:
        raise RuntimeError("Models not loaded — call load_models() first")

    ext = os.path.splitext(filename)[1].lower()
    start = time.perf_counter()

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(file_bytes)
        tmp_path = f.name

    try:
        result = _converter.convert(tmp_path)
        elements = _build_tree(result)
        duration_ms = int((time.perf_counter() - start) * 1000)

        return ParseResponse(
            document=elements,
            metadata=_build_metadata(result, filename, ext, duration_ms),
            errors=[e.error_message for e in result.errors],
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
        status=_enum_value(result.status) or "unknown",
        confidence=_extract_confidence(result),
        binary_hash=str(binary_hash) if binary_hash is not None else None,
    )


def _extract_confidence(result: ConversionResult) -> ParseConfidence | None:
    report = getattr(result, "confidence", None)
    if report is None:
        return None

    grade = _enum_value(getattr(report, "mean_grade", None))
    if grade is None:
        return None

    score = getattr(report, "mean_score", None)
    if score is None or (isinstance(score, float) and math.isnan(score)):
        score = None
    else:
        score = float(score)

    return ParseConfidence(grade=grade, score=score)


def _build_tree(result: ConversionResult) -> list[DocumentElement]:
    from docling_core.types.doc.document import (
        CodeItem,
        DoclingDocument,
        FormulaItem,
        ListItem,
        SectionHeaderItem,
        TableItem,
        TextItem,
    )
    from docling_core.types.doc.labels import DocItemLabel

    doc: DoclingDocument = result.document
    elements: list[DocumentElement] = []

    for item, _level in doc.iterate_items():
        meta = _element_meta(item)
        label = getattr(item, "label", None)

        if isinstance(item, SectionHeaderItem):
            level = item.level if hasattr(item, "level") else 1
            elements.append(DocumentElement(type="heading", level=level, text=item.text, **meta))
        elif isinstance(item, TableItem):
            html = item.export_to_html() if hasattr(item, "export_to_html") else None
            text = item.text if hasattr(item, "text") else None
            elements.append(DocumentElement(type="table", html=html, text=text, **meta))
        elif isinstance(item, ListItem):
            elements.append(DocumentElement(type="list_item", text=item.text, **meta))
        elif isinstance(item, FormulaItem):
            # FormulaItem.text holds the LaTeX produced by formula enrichment.
            elements.append(DocumentElement(type="formula", text=item.text, **meta))
        elif isinstance(item, CodeItem):
            elements.append(
                DocumentElement(
                    type="code", text=item.text, language=_code_language(item), **meta
                )
            )
        elif hasattr(item, "image") and item.image is not None:
            data_uri = _image_to_data_uri(item)
            elements.append(DocumentElement(type="image", data_uri=data_uri, **meta))
        elif isinstance(item, TextItem):
            if label == DocItemLabel.TITLE:
                elements.append(DocumentElement(type="title", text=item.text, **meta))
            elif label == DocItemLabel.CAPTION:
                elements.append(DocumentElement(type="caption", text=item.text, **meta))
            elif label == DocItemLabel.PAGE_HEADER or label == DocItemLabel.PAGE_FOOTER:
                continue
            else:
                elements.append(DocumentElement(type="paragraph", text=item.text, **meta))
        elif hasattr(item, "text") and item.text:
            elements.append(DocumentElement(type="paragraph", text=item.text, **meta))

    return elements


def _element_meta(item: object) -> dict[str, object]:
    """Shared metadata carried by every element: stable ref, page, label, charspan."""
    ref = getattr(item, "self_ref", None)
    label = _enum_value(getattr(item, "label", None))

    page: int | None = None
    charspan: tuple[int, int] | None = None
    prov = getattr(item, "prov", None)
    if isinstance(prov, list) and prov:
        first = prov[0]
        page = getattr(first, "page_no", None)
        span = getattr(first, "charspan", None)
        if span is not None and len(span) == 2:
            charspan = (int(span[0]), int(span[1]))

    return {"ref": ref, "page": page, "label": label, "charspan": charspan}


def _code_language(item: object) -> str | None:
    value = _enum_value(getattr(item, "code_language", None))
    if value is None or value.lower() == "unknown":
        return None
    return value


def _enum_value(value: object) -> str | None:
    """Return ``value.value`` for enums, the string itself for strings, else None."""
    if value is None:
        return None
    return getattr(value, "value", value) if not isinstance(value, str) else value


def _image_to_data_uri(item: object) -> str | None:
    image = getattr(item, "image", None)
    if image is None:
        return None

    pil_image = getattr(image, "pil_image", None)
    if pil_image is None:
        return None

    import io

    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    encoded = base64.b64encode(buf.getvalue()).decode("ascii")
    return f"data:image/png;base64,{encoded}"
