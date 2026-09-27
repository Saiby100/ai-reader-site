from __future__ import annotations

import logging
import re
from collections import Counter

from ..config import settings
from ..models import DocumentElement
from .converter import get_ocr_converter, get_ocr_engine
from .links import Rect
from .tree import build_tree

logger = logging.getLogger(__name__)


def repair_lossy_ligatures(
    file_bytes: bytes,
    tmp_path: str,
    elements: list[DocumentElement],
    errors: list[str],
    links_by_page: dict[int, list[tuple[Rect, int]]],
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
    glyph_words = _collect_glyph_words(file_bytes, set(counts))
    _apply_glyph_map(elements, mapping, glyph_words)
    if unresolved_pages:
        logger.info("Unrecognised glyph(s); OCR backstop on pages %s", sorted(unresolved_pages))
        elements = _splice_ocr_pages(tmp_path, elements, unresolved_pages, errors, links_by_page)
    return elements


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

    engine = get_ocr_engine()
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


def _collect_glyph_words(
    file_bytes: bytes, codes: set[str]
) -> dict[str, list[tuple[str, str]]]:
    """Read the true in-word context of every broken glyph from the raw PDF text layer.

    Docling pads each broken glyph with spaces that are indistinguishable from real word
    boundaries, and it pads inconsistently — so its text alone cannot tell ``After`` (a-ft-er,
    a pad space) from ``came from`` (a real space): both arrive as ``X ⟦⟧ Y``. pdfium's raw
    text layer keeps the original spacing, so for each occurrence we record the contiguous
    word letters touching the glyph as ``(prefix, suffix)`` (lowercased). An *empty* prefix or
    suffix means a real word boundary on that side; a non-empty one means letters Docling
    split off with a pad space. ``_apply_glyph_map`` matches these against the padded Docling
    text to strip only the pads. Keyed by glyph code; values sorted by descending prefix
    length so the longest (most specific) match wins (e.g. 'carefree' over 'free').
    """
    import pypdfium2 as pdfium

    words: dict[str, set[tuple[str, str]]] = {c: set() for c in codes}
    try:
        pdf = pdfium.PdfDocument(file_bytes)
    except Exception:
        logger.warning("Could not open PDF for glyph-boundary scan", exc_info=True)
        return {c: [] for c in codes}
    try:
        for pidx in range(len(pdf)):
            text = pdf[pidx].get_textpage().get_text_range()
            n = len(text)
            for i, ch in enumerate(text):
                if ch not in codes:
                    continue
                a = i
                while a > 0 and _is_word_char(text[a - 1]):
                    a -= 1
                b = i
                while b + 1 < n and _is_word_char(text[b + 1]):
                    b += 1
                words[ch].add((text[a:i].lower(), text[i + 1 : b + 1].lower()))
    except Exception:
        logger.warning("Glyph-boundary scan failed; spacing may be approximate", exc_info=True)
    finally:
        pdf.close()
    return {c: sorted(v, key=lambda ps: -len(ps[0])) for c, v in words.items()}


def _apply_glyph_map(
    elements: list[DocumentElement],
    mapping: dict[str, str],
    glyph_words: dict[str, list[tuple[str, str]]] | None = None,
) -> None:
    """Replace recognised glyphs throughout the tree, stripping only Docling's pad spaces.

    Docling renders an unmapped glyph flanked by inserted spaces ('O ⟦⟧ en' for 'Often',
    'extraordinary ⟦⟧eedom' for 'extraordinary freedom'). Whether a flanking space is a pad to
    drop or a real boundary to keep can't be told from Docling's text, so we match each
    occurrence's surrounding letters against the raw-layer truth from ``_collect_glyph_words``:
    a space is stripped only where the raw layer had letters on that side. With no boundary
    data we keep both spaces (never fuse two words). ``charspan`` is cleared on any rewritten
    element since the text offsets shift.
    """
    if not mapping:
        return
    glyph_words = glyph_words or {}
    cls = "[" + "".join(re.escape(code) for code in mapping) + "]"
    pattern = re.compile(rf" ?{cls} ?")

    def replace(text: str) -> str:
        def sub(m: re.Match[str]) -> str:
            matched = m.group()
            code = next(c for c in matched if c in mapping)
            letters = mapping[code]
            had_lead = matched[0] == " "
            had_trail = matched[-1] == " "

            before = text[: m.start()]
            after = text[m.end() :]
            pa = len(before)
            while pa > 0 and _is_word_char(before[pa - 1]):
                pa -= 1
            cand_prefix = before[pa:].lower()
            pb = 0
            while pb < len(after) and _is_word_char(after[pb]):
                pb += 1
            cand_suffix = after[:pb].lower()

            strip_lead = strip_trail = False
            for prefix, suffix in glyph_words.get(code, ()):
                if cand_prefix.endswith(prefix) and cand_suffix.startswith(suffix):
                    strip_lead = bool(prefix)  # letters before glyph in raw -> leading pad
                    strip_trail = bool(suffix)
                    break

            lead = "" if (had_lead and strip_lead) else (" " if had_lead else "")
            trail = "" if (had_trail and strip_trail) else (" " if had_trail else "")
            return f"{lead}{letters}{trail}"

        return pattern.sub(sub, text)

    def fix(el: DocumentElement) -> None:
        for field in ("text", "html"):
            original = getattr(el, field)
            if not original:
                continue
            updated = replace(original)
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
    links_by_page: dict[int, list[tuple[Rect, int]]],
) -> list[DocumentElement]:
    """Backstop: OCR the given pages full-page and splice them over the text-layer tree.

    Used only for the rare glyph that recognition could not resolve. Elements are merged by
    page, preserving reading order; text-layer elements are kept where OCR yields nothing.
    """
    ocr = get_ocr_converter()
    ocr_by_page: dict[int, list[DocumentElement]] = {}
    for start, end in _contiguous_ranges(sorted(pages)):
        ocr_result = ocr.convert(tmp_path, page_range=(start, end))
        for element in build_tree(ocr_result, links_by_page):
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
