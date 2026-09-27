from __future__ import annotations

from .fakes import _Bbox, _Doc, _Item, _Page, _Prov


def _link_item(page_no: int, left: float, top: float, right: float, bottom: float):
    """An item (with a top-left bbox) + a doc whose page has a known height."""
    item = _Item(
        prov=[_Prov(page_no=page_no, charspan=(0, 1), bbox=_Bbox(left, right, top, bottom))]
    )
    doc = _Doc({page_no: _Page(width=612, height=792)})
    return item, doc


def test_match_link_binds_element_covered_by_link() -> None:
    from app.parsing.links import match_link

    # element bbox sits fully inside the link rect -> coverage 1.0 -> target page bound
    item, doc = _link_item(1, left=72, top=79, right=176, bottom=96)
    links = {1: [((72.0, 72.0, 220.0, 97.0), 2)]}
    assert match_link(item, doc, links) == 2


def test_match_link_skips_below_threshold() -> None:
    from app.parsing.links import match_link

    # link grazes only a small slice of the element -> below 0.5 coverage -> no bind
    item, doc = _link_item(1, left=72, top=79, right=200, bottom=96)
    links = {1: [((180.0, 79.0, 220.0, 96.0), 2)]}
    assert match_link(item, doc, links) is None


def test_match_link_returns_none_without_matching_links_or_geometry() -> None:
    from app.parsing.links import match_link

    item, doc = _link_item(1, left=72, top=79, right=176, bottom=96)
    # empty map, and a link only on a different page
    assert match_link(item, doc, {}) is None
    assert match_link(item, doc, {2: [((0.0, 0.0, 500.0, 500.0), 3)]}) is None
    # link present on the page, but the item carries no bbox
    no_bbox = _Item(prov=[_Prov(page_no=1, charspan=(0, 1))])
    assert match_link(no_bbox, doc, {1: [((0.0, 0.0, 500.0, 500.0), 2)]}) is None


def test_coverage_is_fraction_of_inner_overlapped() -> None:
    from app.parsing.links import _coverage

    # inner fully inside outer -> 1.0
    assert _coverage((10, 10, 20, 20), (0, 0, 100, 100)) == 1.0
    # no overlap -> 0.0
    assert _coverage((0, 0, 10, 10), (50, 50, 60, 60)) == 0.0
    # half of inner's area overlaps outer
    assert _coverage((0, 0, 10, 10), (5, 0, 100, 100)) == 0.5
