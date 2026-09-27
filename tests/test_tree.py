from __future__ import annotations

from .fakes import _Bbox, _Doc, _Enum, _Item, _Page, _Prov, _item_with_bbox


def test_enum_value_handles_enums_strings_and_none() -> None:
    from app.parsing.tree import enum_value

    assert enum_value(_Enum("success")) == "success"
    assert enum_value("good") == "good"
    assert enum_value(None) is None


def test_code_language_drops_unknown() -> None:
    from app.parsing.tree import _code_language

    assert _code_language(_Item(code_language=_Enum("Python"))) == "Python"
    assert _code_language(_Item(code_language=_Enum("unknown"))) is None
    assert _code_language(_Item()) is None


def test_element_meta_extracts_ref_page_label_charspan() -> None:
    from app.parsing.tree import _element_meta

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
    from app.parsing.tree import _element_meta

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
    from app.parsing.tree import _element_meta

    class _Url:
        """Stand-in for Docling's AnyUrl, which stringifies to the href."""

        def __str__(self) -> str:
            return "https://example.com/"

    item = _Item(self_ref="#/texts/3", prov=[_Prov(page_no=1, charspan=(0, 5))], hyperlink=_Url())
    assert _element_meta(item, _Doc())["link_href"] == "https://example.com/"
    # no hyperlink attribute at all -> None
    assert _element_meta(_Item(self_ref="#/x"), _Doc())["link_href"] is None


def test_alignment_detects_center_right_and_default() -> None:
    from app.parsing.tree import _alignment

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
    from app.parsing.tree import _alignment

    # spans 90% of the page -> ordinary body/justified text, not a deliberate alignment
    item, doc = _item_with_bbox(1, left=5, right=95, page_width=100)
    assert _alignment(item, doc) is None


def test_alignment_returns_none_without_geometry() -> None:
    from app.parsing.tree import _alignment

    # no provenance at all (e.g. DOCX/HTML/MD inputs)
    assert _alignment(_Item(self_ref="#/texts/1"), _Doc()) is None
    # bbox present but the page has no known size
    item = _Item(prov=[_Prov(page_no=1, charspan=(0, 1), bbox=_Bbox(40, 60))])
    assert _alignment(item, _Doc()) is None
    # provenance present but no bbox (page size known)
    item = _Item(prov=[_Prov(page_no=1, charspan=(0, 1))])
    assert _alignment(item, _Doc({1: _Page(100)})) is None
