import os

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _set_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SERVICE_SECRET", "test-secret")


@pytest.fixture()
def client() -> TestClient:
    from app.main import app

    return TestClient(app)


AUTH_HEADER = {"Authorization": "Bearer test-secret"}


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "model_loaded" in data


def test_parse_requires_auth(client: TestClient) -> None:
    response = client.post("/parse")
    assert response.status_code == 422


def test_parse_rejects_bad_auth(client: TestClient) -> None:
    response = client.post(
        "/parse",
        headers={"Authorization": "Bearer wrong"},
        files={"file": ("test.pdf", b"fake", "application/pdf")},
    )
    assert response.status_code == 401


def test_parse_rejects_unsupported_extension(client: TestClient) -> None:
    response = client.post(
        "/parse",
        headers=AUTH_HEADER,
        files={"file": ("test.exe", b"fake", "application/octet-stream")},
    )
    assert response.status_code == 415


# --- pure helpers (no model loading) ---


class _Enum:
    def __init__(self, value: str) -> None:
        self.value = value


class _Bbox:
    def __init__(
        self, left: float, right: float, top: float = 0.0, bottom: float = 0.0
    ) -> None:
        self.l = left
        self.r = right
        self.t = top
        self.b = bottom

    def to_top_left_origin(self, page_height: float) -> "_Bbox":
        # Test bboxes are supplied already in top-left coords; identity keeps the
        # overlap math in the assertions easy to read.
        return self


class _Prov:
    def __init__(
        self,
        page_no: int,
        charspan: tuple[int, int],
        bbox: "_Bbox | None" = None,
    ) -> None:
        self.page_no = page_no
        self.charspan = charspan
        self.bbox = bbox


class _Size:
    def __init__(self, width: float, height: float = 0.0) -> None:
        self.width = width
        self.height = height


class _Page:
    def __init__(self, width: float, height: float = 0.0) -> None:
        self.size = _Size(width, height)


class _Doc:
    """Stand-in for a DoclingDocument exposing only ``pages`` (page_no -> page)."""

    def __init__(self, pages: "dict[int, _Page] | None" = None) -> None:
        self.pages = pages or {}


class _Item:
    def __init__(self, **kwargs: object) -> None:
        self.__dict__.update(kwargs)


def _item_with_bbox(page_no: int, left: float, right: float, page_width: float):
    """An item + a doc whose page has the given width, for alignment tests."""
    item = _Item(prov=[_Prov(page_no=page_no, charspan=(0, 1), bbox=_Bbox(left, right))])
    doc = _Doc({page_no: _Page(page_width)})
    return item, doc


def test_enum_value_handles_enums_strings_and_none() -> None:
    from app.parser import _enum_value

    assert _enum_value(_Enum("success")) == "success"
    assert _enum_value("good") == "good"
    assert _enum_value(None) is None


def test_code_language_drops_unknown() -> None:
    from app.parser import _code_language

    assert _code_language(_Item(code_language=_Enum("Python"))) == "Python"
    assert _code_language(_Item(code_language=_Enum("unknown"))) is None
    assert _code_language(_Item()) is None


def test_element_meta_extracts_ref_page_label_charspan() -> None:
    from app.parser import _element_meta

    item = _Item(
        self_ref="#/texts/12",
        label=_Enum("text"),
        prov=[_Prov(page_no=3, charspan=(18, 24))],
    )
    meta = _element_meta(item, _Doc())
    assert meta == {
        "ref": "#/texts/12",
        "page": 3,
        "label": "text",
        "charspan": (18, 24),
        "alignment": None,
        "link_href": None,
    }


def test_element_meta_tolerates_missing_provenance() -> None:
    from app.parser import _element_meta

    meta = _element_meta(_Item(self_ref="#/texts/1"), _Doc())
    assert meta == {
        "ref": "#/texts/1",
        "page": None,
        "label": None,
        "charspan": None,
        "alignment": None,
        "link_href": None,
    }


def test_element_meta_extracts_external_hyperlink() -> None:
    from app.parser import _element_meta

    class _Url:
        """Stand-in for Docling's AnyUrl, which stringifies to the href."""

        def __str__(self) -> str:
            return "https://example.com/"

    item = _Item(self_ref="#/texts/3", prov=[_Prov(page_no=1, charspan=(0, 5))], hyperlink=_Url())
    assert _element_meta(item, _Doc())["link_href"] == "https://example.com/"
    # no hyperlink attribute at all -> None
    assert _element_meta(_Item(self_ref="#/x"), _Doc())["link_href"] is None


def test_alignment_detects_center_right_and_default() -> None:
    from app.parser import _alignment

    # page width 100; symmetric 30-wide margins -> centered block (40..60)
    item, doc = _item_with_bbox(1, left=40, right=60, page_width=100)
    assert _alignment(item, doc) == "center"

    # large left margin, hugging the right edge -> right-aligned (70..98)
    item, doc = _item_with_bbox(1, left=70, right=98, page_width=100)
    assert _alignment(item, doc) == "right"

    # small left margin, trailing whitespace to the right -> left (default) -> None
    item, doc = _item_with_bbox(1, left=2, right=40, page_width=100)
    assert _alignment(item, doc) is None


def test_alignment_ignores_full_width_blocks() -> None:
    from app.parser import _alignment

    # spans 90% of the page -> ordinary body/justified text, not a deliberate alignment
    item, doc = _item_with_bbox(1, left=5, right=95, page_width=100)
    assert _alignment(item, doc) is None


def test_alignment_returns_none_without_geometry() -> None:
    from app.parser import _alignment

    # no provenance at all (e.g. DOCX/HTML/MD inputs)
    assert _alignment(_Item(self_ref="#/texts/1"), _Doc()) is None
    # bbox present but the page has no known size
    item = _Item(prov=[_Prov(page_no=1, charspan=(0, 1), bbox=_Bbox(40, 60))])
    assert _alignment(item, _Doc()) is None
    # provenance present but no bbox (page size known)
    item = _Item(prov=[_Prov(page_no=1, charspan=(0, 1))])
    assert _alignment(item, _Doc({1: _Page(100)})) is None


PUA_FR = ""  # stands in for the 'fr' ligature glyph
PUA_FT = ""  # stands in for the 'ft' ligature glyph


def _el(**kwargs: object):
    from app.models import DocumentElement

    kwargs.setdefault("type", "paragraph")
    return DocumentElement(**kwargs)


def test_collect_pua_counts_across_tree_and_fields() -> None:
    from app.parser import _collect_pua

    tree = [
        _el(text=f"O{PUA_FT}en and A{PUA_FR}ica"),
        _el(
            type="table",
            html=f"<td>{PUA_FR}om</td>",
            children=[_el(text=f"le{PUA_FT}")],
        ),
        _el(text="clean paragraph, no broken glyphs"),
    ]
    counts = _collect_pua(tree)
    assert counts[PUA_FT] == 2  # 'Often' + 'left'
    assert counts[PUA_FR] == 2  # 'Africa' + 'from' (in table html)
    assert sum(counts.values()) == 4


def test_apply_glyph_map_strips_pads_keeps_boundaries_and_clears_charspan() -> None:
    from app.parser import _apply_glyph_map

    mapping = {PUA_FT: "ft", PUA_FR: "fr"}
    # Raw-layer truth (prefix, suffix) per glyph; empty side == real word boundary there.
    # 'often'/'left' are mid-word (pad spaces); 'from' is word-initial (the leading space is
    # a real boundary, identical in Docling's text to the mid-word pad case).
    glyph_words = {
        PUA_FT: [("o", "en"), ("le", "")],  # 'often', 'left'
        PUA_FR: [("", "om")],  # 'from'
    }
    mid = _el(text=f"O {PUA_FT} en", charspan=(0, 5))  # 'Often' -> strip both pads
    initial = _el(text=f"goods {PUA_FR} om here", charspan=(0, 9))  # 'goods from here'
    final = _el(text=f"le {PUA_FT} .", charspan=(0, 4))  # 'left.' -> word-final, keep boundary
    clean = _el(text="untouched", charspan=(0, 9))

    _apply_glyph_map([mid, initial, final, clean], mapping, glyph_words)

    assert mid.text == "Often"
    assert initial.text == "goods from here"
    assert final.text == "left ."
    # rewritten elements drop their now-stale charspan; the clean one keeps it
    assert mid.charspan is None and initial.charspan is None and final.charspan is None
    assert clean.text == "untouched" and clean.charspan == (0, 9)


def test_apply_glyph_map_without_boundary_data_never_fuses_words() -> None:
    from app.parser import _apply_glyph_map

    # With no raw-layer data, a flanking space is kept rather than risk joining two words.
    # This is the word-initial shape Docling actually emits (leading boundary, no trailing pad).
    initial = _el(text=f"extraordinary {PUA_FR}eedom")
    _apply_glyph_map([initial], {PUA_FR: "fr"}, {})
    assert initial.text == "extraordinary freedom"


def test_apply_glyph_map_recurses_into_children() -> None:
    from app.parser import _apply_glyph_map

    glyph_words = {PUA_FR: [("a", "ica")], PUA_FT: [("o", "en")]}  # 'Africa', 'Often'
    parent = _el(text=f"A{PUA_FR}ica", children=[_el(text=f"O{PUA_FT}en")])
    _apply_glyph_map([parent], {PUA_FR: "fr", PUA_FT: "ft"}, glyph_words)
    assert parent.text == "Africa"
    assert parent.children[0].text == "Often"


def test_contiguous_ranges_collapses_runs() -> None:
    from app.parser import _contiguous_ranges

    assert _contiguous_ranges([5, 6, 7, 40]) == [(5, 7), (40, 40)]
    assert _contiguous_ranges([40, 5, 6]) == [(5, 6), (40, 40)]
    assert _contiguous_ranges([]) == []


def _link_item(page_no: int, left: float, top: float, right: float, bottom: float):
    """An item (with a top-left bbox) + a doc whose page has a known height."""
    item = _Item(
        prov=[_Prov(page_no=page_no, charspan=(0, 1), bbox=_Bbox(left, right, top, bottom))]
    )
    doc = _Doc({page_no: _Page(width=612, height=792)})
    return item, doc


def test_match_link_binds_element_covered_by_link() -> None:
    from app.parser import _match_link

    # element bbox sits fully inside the link rect -> coverage 1.0 -> target page bound
    item, doc = _link_item(1, left=72, top=79, right=176, bottom=96)
    links = {1: [((72.0, 72.0, 220.0, 97.0), 2)]}
    assert _match_link(item, doc, links) == 2


def test_match_link_skips_below_threshold() -> None:
    from app.parser import _match_link

    # link grazes only a small slice of the element -> below 0.5 coverage -> no bind
    item, doc = _link_item(1, left=72, top=79, right=200, bottom=96)
    links = {1: [((180.0, 79.0, 220.0, 96.0), 2)]}
    assert _match_link(item, doc, links) is None


def test_match_link_returns_none_without_matching_links_or_geometry() -> None:
    from app.parser import _match_link

    item, doc = _link_item(1, left=72, top=79, right=176, bottom=96)
    # empty map, and a link only on a different page
    assert _match_link(item, doc, {}) is None
    assert _match_link(item, doc, {2: [((0.0, 0.0, 500.0, 500.0), 3)]}) is None
    # link present on the page, but the item carries no bbox
    no_bbox = _Item(prov=[_Prov(page_no=1, charspan=(0, 1))])
    assert _match_link(no_bbox, doc, {1: [((0.0, 0.0, 500.0, 500.0), 2)]}) is None


def test_coverage_is_fraction_of_inner_overlapped() -> None:
    from app.parser import _coverage

    # inner fully inside outer -> 1.0
    assert _coverage((10, 10, 20, 20), (0, 0, 100, 100)) == 1.0
    # no overlap -> 0.0
    assert _coverage((0, 0, 10, 10), (50, 50, 60, 60)) == 0.0
    # half of inner's area overlaps outer
    assert _coverage((0, 0, 10, 10), (5, 0, 100, 100)) == 0.5
