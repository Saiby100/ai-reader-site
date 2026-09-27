from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


# A link must cover at least this fraction of an element's bbox to bind to it — guards against
# a link bleeding onto an adjacent block. Mirrors Docling's own hyperlink-matching threshold
# (intersection-over-element, since link annotation rects are often drawn slightly larger than
# the tight text bbox they sit over).
_LINK_COVERAGE_THRESHOLD = 0.5

# Top-left-origin rectangle (l, t, r, b) with t < b.
Rect = tuple[float, float, float, float]


def extract_pdf_links(file_bytes: bytes) -> dict[int, list[tuple[Rect, int]]]:
    """Pull internal /GoTo link annotations from a PDF, keyed by 1-based source page.

    Docling drops these (its parser resolves a /URI but leaves a /GoTo's ``uri`` ``None``, and
    the page assembler skips null URIs), so we read them straight from the PDF with pypdfium2
    — already a dependency. Each entry is ``(rect, target_page)`` where ``rect`` is normalized
    to top-left origin and ``target_page`` is 1-based. External /URI links are handled
    separately via Docling's ``TextItem.hyperlink`` (see ``_element_meta``). Best-effort: any
    failure yields ``{}`` so link extraction never blocks a parse.
    """
    import ctypes

    import pypdfium2 as pdfium
    import pypdfium2.raw as pr

    links: dict[int, list[tuple[Rect, int]]] = {}
    try:
        pdf = pdfium.PdfDocument(file_bytes)
    except Exception:
        logger.warning("Could not open PDF for link extraction", exc_info=True)
        return {}

    try:
        for pidx in range(len(pdf)):
            page = pdf[pidx]
            page_height = page.get_size()[1]
            pos = ctypes.c_int(0)
            link = pr.FPDF_LINK()
            page_links: list[tuple[Rect, int]] = []
            while pr.FPDFLink_Enumerate(page.raw, ctypes.byref(pos), ctypes.byref(link)):
                dest = pr.FPDFLink_GetDest(pdf.raw, link)
                if not dest:
                    continue  # not an internal destination (e.g. a /URI link)
                target = pr.FPDFDest_GetDestPageIndex(pdf.raw, dest)
                if target < 0:
                    continue
                rect = pr.FS_RECTF()
                if not pr.FPDFLink_GetAnnotRect(link, ctypes.byref(rect)):
                    continue
                # FS_RECTF is bottom-left origin (top > bottom); flip to top-left.
                top_left: Rect = (
                    rect.left,
                    page_height - rect.top,
                    rect.right,
                    page_height - rect.bottom,
                )
                page_links.append((top_left, target + 1))
            if page_links:
                links[pidx + 1] = page_links
    except Exception:
        logger.warning("PDF link extraction failed; continuing without links", exc_info=True)
        return {}
    finally:
        pdf.close()

    return links


def match_link(
    item: object, doc: object, links_by_page: dict[int, list[tuple[Rect, int]]]
) -> int | None:
    """Resolve the internal-link target page for ``item`` by spatial overlap, or ``None``.

    Picks the /GoTo link on the item's page whose rect is most covered by the item's bounding
    box, above ``_LINK_COVERAGE_THRESHOLD``. Docling collapses a text cluster into one element,
    so the whole element inherits the link — precise for TOC lines, coarse for an inline link
    buried in a larger paragraph (a known limitation).
    """
    if not links_by_page:
        return None

    prov = getattr(item, "prov", None)
    if not isinstance(prov, list) or not prov:
        return None
    page_no = getattr(prov[0], "page_no", None)
    bbox = getattr(prov[0], "bbox", None)
    page_links = links_by_page.get(page_no)
    if not page_links or bbox is None:
        return None

    pages = getattr(doc, "pages", None)
    page = pages.get(page_no) if hasattr(pages, "get") else None
    page_height = getattr(getattr(page, "size", None), "height", None)
    if not page_height:
        return None

    tl = bbox.to_top_left_origin(page_height)
    el_rect: Rect = (tl.l, tl.t, tl.r, tl.b)

    best_page: int | None = None
    best_cov = _LINK_COVERAGE_THRESHOLD
    for link_rect, target_page in page_links:
        cov = _coverage(el_rect, link_rect)
        if cov >= best_cov:
            best_cov = cov
            best_page = target_page
    return best_page


# Matches one table cell tag and its inner HTML: (open tag, tag name, inner, close tag).
# Non-greedy + DOTALL; the 1:1 tag/cell count guard in ``_inject_cell_links`` keeps this from
# being applied to tables whose cells nest markup the simple match can't bracket.
_CELL_TAG_RE = re.compile(r"(<(t[dh])\b[^>]*>)(.*?)(</\2\s*>)", re.DOTALL | re.IGNORECASE)


def table_html_with_links(
    item: object,
    doc: object,
    links_by_page: dict[int, list[tuple[Rect, int]]],
) -> str | None:
    """Export a table to HTML, wrapping each cell that sits over a /GoTo link in a page-jump anchor.

    Pass ``doc``: the no-arg ``export_to_html()`` is deprecated and returns an empty string for
    some tables (e.g. a ``document_index`` TOC), silently dropping them. Beyond that, Docling
    collapses a whole table into one element, so a TOC's per-row links would be lost — one element
    carries only one ``link_target_page``. We match each cell's bbox against the page's link rects
    (the coverage test from ``match_link``) and inject ``<a data-link-page>`` into the exported
    HTML. Cells align to Docling's ``<td>``/``<th>`` tags by document order; injection is skipped
    (HTML returned unchanged) unless that 1:1 alignment holds and at least one cell matches a link,
    so ordinary tables are untouched.
    """
    html = item.export_to_html(doc=doc) if hasattr(item, "export_to_html") else None
    if not html or not links_by_page:
        return html

    data = getattr(item, "data", None)
    cells = list(getattr(data, "table_cells", None) or [])
    prov = getattr(item, "prov", None)
    page_no = getattr(prov[0], "page_no", None) if isinstance(prov, list) and prov else None
    page_links = links_by_page.get(page_no) if page_no else None
    if not cells or not page_links:
        return html

    pages = getattr(doc, "pages", None)
    page = pages.get(page_no) if hasattr(pages, "get") else None
    page_height = getattr(getattr(page, "size", None), "height", None)

    targets = [_cell_link_target(cell, page_links, page_height) for cell in cells]
    if not any(t is not None for t in targets):
        return html
    return _inject_cell_links(html, targets)


def _coverage(inner: Rect, outer: Rect) -> float:
    """Fraction of ``inner``'s area that overlaps ``outer`` (both top-left origin)."""
    ix = max(0.0, min(inner[2], outer[2]) - max(inner[0], outer[0]))
    iy = max(0.0, min(inner[3], outer[3]) - max(inner[1], outer[1]))
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return (ix * iy) / area if area > 0 else 0.0


def _cell_link_target(
    cell: object, page_links: list[tuple[Rect, int]], page_height: float | None
) -> int | None:
    """Target page of the /GoTo link most covered by ``cell``'s bbox, above the threshold, or None."""
    bbox = getattr(cell, "bbox", None)
    if bbox is None:
        return None
    origin = getattr(getattr(bbox, "coord_origin", None), "value", None)
    if origin == "BOTTOMLEFT" and page_height:
        bbox = bbox.to_top_left_origin(page_height)
    rect: Rect = (bbox.l, bbox.t, bbox.r, bbox.b)

    best: int | None = None
    best_cov = _LINK_COVERAGE_THRESHOLD
    for link_rect, target in page_links:
        cov = _coverage(rect, link_rect)
        if cov >= best_cov:
            best_cov = cov
            best = target
    return best


def _inject_cell_links(html: str, targets: list[int | None]) -> str:
    """Wrap each cell's inner HTML in a page-jump anchor where ``targets`` has a page.

    ``targets`` is indexed by document order of the table's cells; it must line up 1:1 with the
    ``<td>``/``<th>`` tags Docling emitted, or we return the HTML untouched rather than risk
    mangling a table whose structure the simple tag scan can't track.
    """
    if len(_CELL_TAG_RE.findall(html)) != len(targets):
        return html

    it = iter(targets)

    def repl(m: re.Match[str]) -> str:
        target = next(it)
        if target is None:
            return m.group(0)
        open_tag, inner, close_tag = m.group(1), m.group(3), m.group(4)
        return f'{open_tag}<a href="#" data-link-page="{target}">{inner}</a>{close_tag}'

    return _CELL_TAG_RE.sub(repl, html)
