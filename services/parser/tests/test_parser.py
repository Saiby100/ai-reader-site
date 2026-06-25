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
    def __init__(self, left: float, right: float) -> None:
        self.l = left
        self.r = right


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
    def __init__(self, width: float) -> None:
        self.width = width


class _Page:
    def __init__(self, width: float) -> None:
        self.size = _Size(width)


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
    }


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


def test_apply_glyph_map_absorbs_pad_spaces_and_clears_charspan() -> None:
    from app.parser import _apply_glyph_map

    mapping = {PUA_FT: "ft", PUA_FR: "fr"}
    # Docling pads the glyph with a space on each side; a real word boundary stays separate.
    mid = _el(text=f"O {PUA_FT} en", charspan=(0, 5))  # 'Often'
    initial = _el(text=f"goods  {PUA_FR} om here", charspan=(0, 9))  # '... goods from here'
    final = _el(text=f"le {PUA_FT} .", charspan=(0, 4))  # 'left.'
    clean = _el(text="untouched", charspan=(0, 9))

    _apply_glyph_map([mid, initial, final, clean], mapping)

    assert mid.text == "Often"
    assert initial.text == "goods from here"
    assert final.text == "left."
    # rewritten elements drop their now-stale charspan; the clean one keeps it
    assert mid.charspan is None and initial.charspan is None and final.charspan is None
    assert clean.text == "untouched" and clean.charspan == (0, 9)


def test_apply_glyph_map_recurses_into_children() -> None:
    from app.parser import _apply_glyph_map

    parent = _el(text=f"A{PUA_FR}ica", children=[_el(text=f"O{PUA_FT}en")])
    _apply_glyph_map([parent], {PUA_FR: "fr", PUA_FT: "ft"})
    assert parent.text == "Africa"
    assert parent.children[0].text == "Often"


def test_contiguous_ranges_collapses_runs() -> None:
    from app.parser import _contiguous_ranges

    assert _contiguous_ranges([5, 6, 7, 40]) == [(5, 7), (40, 40)]
    assert _contiguous_ranges([40, 5, 6]) == [(5, 6), (40, 40)]
    assert _contiguous_ranges([]) == []
