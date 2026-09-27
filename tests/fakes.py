"""Hand-rolled stand-ins for the Docling objects the parser reads.

Kept deliberately minimal — each fake exposes only the attributes the code under test
touches — so the unit tests run without importing Docling or loading any model. Extend
these rather than reaching for the real types.
"""

from __future__ import annotations

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
