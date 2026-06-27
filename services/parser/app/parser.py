import base64
import logging
import math
import os
import re
import tempfile
import time
from collections import Counter

from docling.datamodel.accelerator_options import AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

from .config import settings
from .models import DocumentElement, ParseConfidence, ParseMetadata, ParseResponse

logger = logging.getLogger(__name__)

_converter: DocumentConverter | None = None
# Built lazily on the first lossy-text-layer document — most PDFs never need it, so we
# avoid loading the OCR models at startup.
_ocr_converter: DocumentConverter | None = None
# Bare RapidOCR engine for recognising individual glyph crops; built lazily (see
# _get_ocr_engine). Distinct from _ocr_converter, which is Docling's full-page OCR pipeline.
_ocr_engine = None


def _make_converter(*, force_full_page_ocr: bool = False) -> DocumentConverter:
    """Build a Docling converter for PDFs.

    The default converter is tuned for ordinary ebooks (text + images): image
    extraction is on (cheap) so figures survive, while OCR and formula/code enrichment
    default off because they are CPU-heavy and unnecessary for born-digital documents.
    Enrichment runs a vision-language model per equation/code block and can peg a CPU
    machine, so it is opt-in via ``settings.enable_enrichment`` for capable (ideally GPU)
    hardware.

    When ``force_full_page_ocr`` is set, the converter ignores the (possibly lossy) text
    layer and OCRs every page with RapidOCR. This is the backstop for PDFs whose embedded
    fonts have broken ligature mappings — see ``_repair_lossy_ligatures``.
    """
    options = PdfPipelineOptions()
    options.do_formula_enrichment = settings.enable_enrichment
    options.do_code_enrichment = settings.enable_enrichment
    options.do_ocr = settings.do_ocr or force_full_page_ocr
    if force_full_page_ocr:
        options.ocr_options = RapidOcrOptions(force_full_page_ocr=True)
    options.generate_picture_images = settings.generate_picture_images
    options.images_scale = settings.images_scale
    options.accelerator_options = AcceleratorOptions(
        device=settings.accelerator_device,
        num_threads=settings.num_threads,
    )
    return DocumentConverter(
        format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)}
    )


def _get_ocr_converter() -> DocumentConverter:
    """Return the full-page-OCR converter, building and warming it on first use."""
    global _ocr_converter
    if _ocr_converter is None:
        logger.info("Building full-page OCR fallback converter (RapidOCR)...")
        _ocr_converter = _make_converter(force_full_page_ocr=True)
        _ocr_converter.initialize_pipeline(InputFormat.PDF)
        logger.info("OCR fallback converter ready")
    return _ocr_converter


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


def _is_pua(ch: str) -> bool:
    """True for a Private Use Area codepoint (U+E000–U+F8FF)."""
    return len(ch) == 1 and 0xE000 <= ord(ch) <= 0xF8FF


def _is_word_char(ch: str) -> bool:
    """A glyph that can sit inside a word: a letter or a broken (PUA) glyph."""
    return ch.isalpha() or _is_pua(ch)


def _collect_pua(elements: list[DocumentElement]) -> Counter[str]:
    """Count every Private Use Area codepoint across an element tree.

    Re-encoded PDFs (often pirated ebooks) embed fonts whose f-ligature glyphs (ft, fr, fi,
    fl, ff) carry no real ToUnicode mapping, so every reader falls back to a PUA codepoint
    (e.g. U+F26D) that has no meaning on its own — 'Often' -> 'O⟦⟧en', 'from' -> '⟦⟧om'.
    Docling preserves the codepoint in its text, so this is both the damage signal and the
    set of glyphs to recognise (see ``_resolve_glyph_map``).
    """
    counts: Counter[str] = Counter()

    def walk(el: DocumentElement) -> None:
        for text in (el.text, el.html):
            if text:
                counts.update(ch for ch in text if _is_pua(ch))
        for child in el.children:
            walk(child)

    for el in elements:
        walk(el)
    return counts


def _get_ocr_engine():
    """Lazily build the RapidOCR engine used to recognise individual glyph crops.

    Distinct from ``_get_ocr_converter`` (Docling's full-page OCR converter, used only as a
    backstop): this is a bare RapidOCR instance we call directly on small word images.
    """
    global _ocr_engine
    if _ocr_engine is None:
        from rapidocr import RapidOCR

        logger.info("Building RapidOCR engine for glyph recognition...")
        _ocr_engine = RapidOCR()
    return _ocr_engine


def _recognize_occurrence(
    chars: list[str],
    boxes: list[tuple[float, float, float, float]],
    i: int,
    pil: object,
    page_height: float,
    engine: object,
    np: object,
) -> str | None:
    """Read the letters of the broken glyph at ``chars[i]`` from the rendered page.

    OCRs the whole text line containing the glyph (engines need word/line context, not an
    isolated glyph), then recovers the glyph's letters by matching the word's intact letters
    as anchors. Returns the 1–4 letter substitution, or None if the line can't be read.
    """
    n = len(chars)
    a = i
    while a > 0 and _is_word_char(chars[a - 1]):
        a -= 1
    b = i
    while b + 1 < n and _is_word_char(chars[b + 1]):
        b += 1

    # Crop the whole text line (boxes vertically overlapping the glyph) for OCR context.
    glyph_bottom, glyph_top = boxes[i][1], boxes[i][3]
    line = [bx for bx in boxes if bx[3] > glyph_bottom and bx[1] < glyph_top]
    if not line:
        return None
    scale = settings.glyph_render_scale
    left = min(bx[0] for bx in line)
    right = max(bx[2] for bx in line)
    bottom = min(bx[1] for bx in line)
    top = max(bx[3] for bx in line)
    pad = 4
    crop = pil.crop(
        (
            int(left * scale) - pad,
            int((page_height - top) * scale) - pad,
            int(right * scale) + pad,
            int((page_height - bottom) * scale) + pad,
        )
    )
    result = engine(np.array(crop))
    text = " ".join(result.txts) if (result and result.txts) else ""
    if not text:
        return None

    # The word is prefix + ⟦glyph⟧ + suffix; the intact letters anchor the glyph's value.
    prefix = "".join(chars[a:i])
    suffix = "".join(chars[i + 1 : b + 1])
    pattern = rf"\b{re.escape(prefix)}([A-Za-z]{{1,4}}){re.escape(suffix)}\b"
    match = re.search(pattern, text)
    return match.group(1) if match else None


def _resolve_glyph_map(
    file_bytes: bytes, codes: set[str]
) -> tuple[dict[str, str], set[int]]:
    """Recognise each unique broken glyph once, by OCR'ing words that contain it.

    Each PUA code is consistent within a document (one code = one ligature), so a handful of
    samples and a majority vote pin down its letters; one mapping then repairs every
    occurrence. Returns ``(code -> letters, unresolved_pages)`` — the 1-based pages holding
    any code we could not read, for the OCR backstop.
    """
    import numpy as np
    import pypdfium2 as pdfium

    engine = _get_ocr_engine()
    pdf = pdfium.PdfDocument(file_bytes)
    try:
        readings: dict[str, list[str]] = {c: [] for c in codes}
        code_pages: dict[str, set[int]] = {c: set() for c in codes}
        samples = settings.glyph_ocr_samples

        for pidx in range(len(pdf)):
            page = pdf[pidx]
            tp = page.get_textpage()
            present = {c for c in codes if c in tp.get_text_range()}
            if not present:
                continue
            for c in present:
                code_pages[c].add(pidx + 1)

            need = {c for c in present if len(readings[c]) < samples}
            if not need:
                continue

            # Build a char list index-aligned with get_charbox (avoids \r\n offset drift).
            n = tp.count_chars()
            chars = [tp.get_text_range(j, 1) for j in range(n)]
            boxes = [tp.get_charbox(j) for j in range(n)]
            pil = page.render(scale=settings.glyph_render_scale).to_pil().convert("RGB")
            page_height = page.get_size()[1]

            for j, ch in enumerate(chars):
                if ch not in need:
                    continue
                value = _recognize_occurrence(chars, boxes, j, pil, page_height, engine, np)
                if value:
                    readings[ch].append(value)
                    if len(readings[ch]) >= samples:
                        need.discard(ch)
                        if not need:
                            break

        mapping: dict[str, str] = {}
        unresolved: set[int] = set()
        for code in codes:
            if readings[code]:
                # TODO(cross-font collision): disagreeing samples can mean two different
                # glyphs share one synthesized PUA value across fonts. We currently take the
                # majority and replace globally; revisit to resolve per-occurrence.
                value, _ = Counter(readings[code]).most_common(1)[0]
                mapping[code] = value
            else:
                unresolved |= code_pages[code]
        return mapping, unresolved
    finally:
        pdf.close()


def _apply_glyph_map(elements: list[DocumentElement], mapping: dict[str, str]) -> None:
    """Replace recognised glyphs throughout the tree, absorbing Docling's pad spaces.

    Docling renders an unmapped glyph flanked by an inserted space on each side
    ('O ⟦⟧ en'); stripping one optional space on each side restores 'Often' while leaving
    real word-boundary spaces (which Docling keeps separately) intact. ``charspan`` is
    cleared on any rewritten element since the text offsets shift.
    """
    if not mapping:
        return
    subs = [
        (re.compile(rf" ?{re.escape(code)} ?"), letters)
        for code, letters in mapping.items()
    ]

    def fix(el: DocumentElement) -> None:
        for field in ("text", "html"):
            original = getattr(el, field)
            if not original:
                continue
            updated = original
            for pattern, letters in subs:
                updated = pattern.sub(letters, updated)
            if updated != original:
                setattr(el, field, updated)
                el.charspan = None
        for child in el.children:
            fix(child)

    for el in elements:
        fix(el)


def _contiguous_ranges(pages: list[int]) -> list[tuple[int, int]]:
    """Collapse sorted page numbers into inclusive (start, end) runs to minimise OCR passes."""
    ranges: list[tuple[int, int]] = []
    for page in sorted(pages):
        if ranges and page == ranges[-1][1] + 1:
            ranges[-1] = (ranges[-1][0], page)
        else:
            ranges.append((page, page))
    return ranges


def _splice_ocr_pages(
    tmp_path: str,
    elements: list[DocumentElement],
    pages: set[int],
    errors: list[str],
    links_by_page: dict[int, list[tuple["Rect", int]]],
) -> list[DocumentElement]:
    """Backstop: OCR the given pages full-page and splice them over the text-layer tree.

    Used only for the rare glyph that recognition could not resolve. Elements are merged by
    page, preserving reading order; text-layer elements are kept where OCR yields nothing.
    """
    ocr = _get_ocr_converter()
    ocr_by_page: dict[int, list[DocumentElement]] = {}
    for start, end in _contiguous_ranges(sorted(pages)):
        ocr_result = ocr.convert(tmp_path, page_range=(start, end))
        for element in _build_tree(ocr_result, links_by_page):
            if element.page is not None:
                ocr_by_page.setdefault(element.page, []).append(element)
        errors.extend(e.error_message for e in ocr_result.errors)

    merged: list[DocumentElement] = []
    spliced: set[int] = set()
    for element in elements:
        page = element.page
        if page in pages and ocr_by_page.get(page):
            if page not in spliced:
                merged.extend(ocr_by_page[page])
                spliced.add(page)
        else:
            merged.append(element)
    return merged


def _repair_lossy_ligatures(
    file_bytes: bytes,
    tmp_path: str,
    elements: list[DocumentElement],
    errors: list[str],
    links_by_page: dict[int, list[tuple["Rect", int]]],
) -> list[DocumentElement]:
    """Recover ligatures lost to broken font mappings.

    Recognises each broken glyph once via OCR and replaces it everywhere (see
    ``_collect_pua`` for the underlying font problem); any glyph that can't be recognised
    falls back to full-page OCR of its pages. Best-effort — a recovery failure never blocks
    the parse, it just leaves the (degraded) text layer in place.
    """
    counts = _collect_pua(elements)
    total = sum(counts.values())
    if total < settings.ocr_fallback_pua_threshold:
        return elements

    try:
        mapping, unresolved_pages = _resolve_glyph_map(file_bytes, set(counts))
    except Exception:
        logger.warning("Ligature recovery failed; leaving text layer as-is", exc_info=True)
        return elements

    logger.info(
        "Recovered %d/%d broken glyph(s) from %d PUA char(s): %s",
        len(mapping),
        len(counts),
        total,
        {f"U+{ord(k):04X}": v for k, v in mapping.items()},
    )
    _apply_glyph_map(elements, mapping)
    if unresolved_pages:
        logger.info("Unrecognised glyph(s); OCR backstop on pages %s", sorted(unresolved_pages))
        elements = _splice_ocr_pages(tmp_path, elements, unresolved_pages, errors, links_by_page)
    return elements


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
        links = _extract_pdf_links(file_bytes) if ext == ".pdf" else {}
        elements = _build_tree(result, links)
        errors = [e.error_message for e in result.errors]

        if ext == ".pdf" and settings.ocr_fallback:
            elements = _repair_lossy_ligatures(file_bytes, tmp_path, elements, errors, links)

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


def _build_tree(
    result: ConversionResult,
    links_by_page: dict[int, list[tuple["Rect", int]]] | None = None,
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
        meta["link_target_page"] = _match_link(item, doc, links_by_page or {})
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


def _element_meta(item: object, doc: object) -> dict[str, object]:
    """Shared metadata carried by every element: ref, page, label, charspan, alignment,
    link_href. The internal-link target (``link_target_page``) is added in ``_build_tree``,
    which has the page-keyed link map."""
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


# A link must cover at least this fraction of an element's bbox to bind to it — guards against
# a link bleeding onto an adjacent block. Mirrors Docling's own hyperlink-matching threshold
# (intersection-over-element, since link annotation rects are often drawn slightly larger than
# the tight text bbox they sit over).
_LINK_COVERAGE_THRESHOLD = 0.5

# Top-left-origin rectangle (l, t, r, b) with t < b.
Rect = tuple[float, float, float, float]


def _coverage(inner: Rect, outer: Rect) -> float:
    """Fraction of ``inner``'s area that overlaps ``outer`` (both top-left origin)."""
    ix = max(0.0, min(inner[2], outer[2]) - max(inner[0], outer[0]))
    iy = max(0.0, min(inner[3], outer[3]) - max(inner[1], outer[1]))
    area = (inner[2] - inner[0]) * (inner[3] - inner[1])
    return (ix * iy) / area if area > 0 else 0.0


def _extract_pdf_links(file_bytes: bytes) -> dict[int, list[tuple[Rect, int]]]:
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


def _match_link(
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
