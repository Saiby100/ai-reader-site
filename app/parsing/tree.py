from __future__ import annotations

import base64

from docling.datamodel.document import ConversionResult

from ..models import DocumentElement
from .links import Rect, match_link, table_html_with_links

def build_tree(
    result: ConversionResult,
    links_by_page: dict[int, list[tuple[Rect, int]]] | None = None,
) -> list[DocumentElement]:
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
        meta = _element_meta(item, doc)
        meta["link_target_page"] = match_link(item, doc, links_by_page or {})
        label = getattr(item, "label", None)

        if isinstance(item, SectionHeaderItem):
            level = item.level if hasattr(item, "level") else 1
            elements.append(DocumentElement(type="heading", level=level, text=item.text, **meta))
        elif isinstance(item, TableItem):
            html = table_html_with_links(item, doc, links_by_page or {})
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


def enum_value(value: object) -> str | None:
    """Return ``value.value`` for enums, the string itself for strings, else None."""
    if value is None:
        return None
    return getattr(value, "value", value) if not isinstance(value, str) else value


def _element_meta(item: object, doc: object) -> dict[str, object]:
    """Shared metadata carried by every element: ref, page, label, charspan, alignment,
    link_href. The internal-link target (``link_target_page``) is added in ``build_tree``,
    which has the page-keyed link map."""
    ref = getattr(item, "self_ref", None)
    label = enum_value(getattr(item, "label", None))

    page: int | None = None
    charspan: tuple[int, int] | None = None
    prov = getattr(item, "prov", None)
    if isinstance(prov, list) and prov:
        first = prov[0]
        page = getattr(first, "page_no", None)
        span = getattr(first, "charspan", None)
        if span is not None and len(span) == 2:
            charspan = (int(span[0]), int(span[1]))

    hyperlink = getattr(item, "hyperlink", None)

    return {
        "ref": ref,
        "page": page,
        "label": label,
        "charspan": charspan,
        "alignment": _alignment(item, doc),
        "link_href": str(hyperlink) if hyperlink else None,
    }


def _alignment(item: object, doc: object) -> str | None:
    """Infer horizontal text alignment ('center' / 'right') from the item's geometry.

    Docling exposes no alignment attribute, so we derive it from the element's bounding box
    relative to its page width: a block with roughly symmetric left/right margins is centered,
    one pushed toward the right is right-aligned. Full-width blocks (ordinary body/justified
    text) and the default left case return ``None`` to keep the contract lean. Returns ``None``
    whenever geometry is unavailable (e.g. DOCX/HTML/MD inputs carry no bbox). Only the
    horizontal edges ``l``/``r`` are used, so the bbox ``coord_origin`` is irrelevant.
    """
    prov = getattr(item, "prov", None)
    if not isinstance(prov, list) or not prov:
        return None

    bbox = getattr(prov[0], "bbox", None)
    page_no = getattr(prov[0], "page_no", None)
    if bbox is None or page_no is None:
        return None

    pages = getattr(doc, "pages", None)
    page = pages.get(page_no) if hasattr(pages, "get") else None
    size = getattr(page, "size", None)
    page_width = getattr(size, "width", None)
    if not page_width:
        return None

    left = getattr(bbox, "l", None)
    right = getattr(bbox, "r", None)
    if left is None or right is None:
        return None

    block_width = right - left
    if block_width >= 0.85 * page_width:
        return None  # full-width body/justified text — not a deliberate alignment

    left_margin = left
    right_margin = page_width - right
    tol = 0.05 * page_width
    if abs(left_margin - right_margin) <= tol:
        return "center"
    if left_margin > right_margin:
        return "right"
    return None


def _code_language(item: object) -> str | None:
    value = enum_value(getattr(item, "code_language", None))
    if value is None or value.lower() == "unknown":
        return None
    return value


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
