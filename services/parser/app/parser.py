import base64
import logging
import os
import tempfile
import time

from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from .models import BoundingBox, DocumentElement, ParseMetadata, ParseResponse

logger = logging.getLogger(__name__)

_converter: DocumentConverter | None = None


def _make_converter() -> DocumentConverter:
    """Build the single Docling converter used for all documents.

    Formula and code enrichment are always on: they self-gate per item (only
    elements labelled FORMULA/CODE are processed and cropped on demand), so they
    add no per-document cost to prose documents while making equations available
    as LaTeX. Keeping a single converter avoids duplicating the heavy base layout
    and table models across pipelines.
    """
    options = PdfPipelineOptions()
    options.do_formula_enrichment = True
    options.do_code_enrichment = True
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def load_models() -> None:
    global _converter
    logger.info("Loading Docling models (with formula + code enrichment)...")
    _converter = _make_converter()
    # Force model loading now (construction is lazy) so the first request — math
    # or otherwise — isn't slowed by model initialization.
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

        page_count = result.document.num_pages() if hasattr(result.document, "num_pages") else 0

        return ParseResponse(
            document=elements,
            metadata=ParseMetadata(
                filename=filename,
                page_count=page_count,
                format_detected=ext.lstrip("."),
                parse_duration_ms=duration_ms,
            ),
            errors=[],
        )
    except Exception:
        logger.exception("Failed to parse %s", filename)
        raise
    finally:
        os.unlink(tmp_path)


def _build_tree(result: ConversionResult) -> list[DocumentElement]:
    from docling_core.types.doc.document import (
        DoclingDocument,
        ListItem,
        SectionHeaderItem,
        TableItem,
        TextItem,
    )
    from docling_core.types.doc.labels import DocItemLabel

    doc: DoclingDocument = result.document
    elements: list[DocumentElement] = []

    for item, _level in doc.iterate_items():
        bbox = _extract_bbox(item)
        page = _extract_page(item)

        if isinstance(item, SectionHeaderItem):
            level = item.level if hasattr(item, "level") else 1
            elements.append(DocumentElement(
                type="heading",
                level=level,
                text=item.text,
                bbox=bbox,
                page=page,
            ))
        elif isinstance(item, TableItem):
            html = item.export_to_html() if hasattr(item, "export_to_html") else None
            text = item.text if hasattr(item, "text") else None
            elements.append(DocumentElement(
                type="table",
                html=html,
                text=text,
                bbox=bbox,
                page=page,
            ))
        elif isinstance(item, ListItem):
            elements.append(DocumentElement(
                type="list_item",
                text=item.text,
                bbox=bbox,
                page=page,
            ))
        elif hasattr(item, "image") and item.image is not None:
            data_uri = _image_to_data_uri(item)
            elements.append(DocumentElement(
                type="image",
                data_uri=data_uri,
                bbox=bbox,
                page=page,
            ))
        elif isinstance(item, TextItem):
            label = item.label if hasattr(item, "label") else None
            if label == DocItemLabel.TITLE:
                elements.append(DocumentElement(
                    type="title",
                    text=item.text,
                    bbox=bbox,
                    page=page,
                ))
            elif label == DocItemLabel.CODE:
                elements.append(DocumentElement(
                    type="code_block",
                    text=item.text,
                    bbox=bbox,
                    page=page,
                ))
            elif label == DocItemLabel.PAGE_HEADER or label == DocItemLabel.PAGE_FOOTER:
                continue
            else:
                elements.append(DocumentElement(
                    type="paragraph",
                    text=item.text,
                    bbox=bbox,
                    page=page,
                ))
        elif hasattr(item, "text") and item.text:
            elements.append(DocumentElement(
                type="paragraph",
                text=item.text,
                bbox=bbox,
                page=page,
            ))

    return elements


def _extract_bbox(item: object) -> BoundingBox | None:
    prov = getattr(item, "prov", None)
    if not prov or not isinstance(prov, list) or len(prov) == 0:
        return None

    first = prov[0]
    bbox_obj = getattr(first, "bbox", None)
    if bbox_obj is None:
        return None

    page_no = getattr(first, "page_no", 0)
    l_val = getattr(bbox_obj, "l", 0.0)
    t_val = getattr(bbox_obj, "t", 0.0)
    r_val = getattr(bbox_obj, "r", 0.0)
    b_val = getattr(bbox_obj, "b", 0.0)

    return BoundingBox(
        x=l_val,
        y=t_val,
        width=r_val - l_val,
        height=b_val - t_val,
        page=page_no,
    )


def _extract_page(item: object) -> int | None:
    prov = getattr(item, "prov", None)
    if not prov or not isinstance(prov, list) or len(prov) == 0:
        return None
    return getattr(prov[0], "page_no", None)


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
