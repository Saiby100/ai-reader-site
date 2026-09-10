"""Tests for the standalone HTML renderer.

These build ``DocumentElement`` instances directly — no Docling involved — so they cover the
markup contract only: which tag each element type produces, which attributes survive, and
what is escaped versus passed through verbatim.
"""

from __future__ import annotations

from typing import get_args

import pytest

from app.models import DocumentElement, ElementType, ParseMetadata, ParseResponse
from app.render_html import RENDERERS, render_body, render_page


def _el(type_: str, **kwargs) -> DocumentElement:
    return DocumentElement(type=type_, **kwargs)


def test_registry_covers_every_element_type():
    assert set(RENDERERS) == set(get_args(ElementType))


@pytest.mark.parametrize(
    ("element", "expected"),
    [
        (_el("title", text="Hi"), "<h1>Hi</h1>"),
        (_el("heading", text="Hi", level=3), "<h3>Hi</h3>"),
        (_el("paragraph", text="Hi"), "<p>Hi</p>"),
        (_el("list_item", text="Hi"), "<li>Hi</li>"),
        (_el("caption", text="Hi"), "<figcaption>Hi</figcaption>"),
        (_el("formula", text="E=mc^2"), "<span data-formula>E=mc^2</span>"),
    ],
)
def test_simple_elements_render_expected_tag(element, expected):
    assert render_body([element]) == expected


def test_heading_level_is_clamped_to_the_valid_range():
    assert render_body([_el("heading", text="x", level=9)]).startswith("<h6")
    assert render_body([_el("heading", text="x", level=0)]).startswith("<h1")


def test_ref_and_page_are_emitted_as_data_attributes():
    html = render_body([_el("paragraph", text="x", ref="#/texts/12", page=4)])
    assert 'data-ref="#/texts/12"' in html
    assert 'data-page="4"' in html


def test_alignment_becomes_a_text_align_rule():
    html = render_body([_el("paragraph", text="x", alignment="center")])
    assert 'style="text-align:center"' in html


def test_text_is_escaped():
    html = render_body([_el("paragraph", text="a < b & c")])
    assert html == "<p>a &lt; b &amp; c</p>"


def test_table_html_passes_through_unescaped():
    html = render_body([_el("table", html="<table><tr><td>1</td></tr></table>")])
    assert "<table><tr><td>1</td></tr></table>" in html


def test_image_data_uri_passes_through_and_is_zoomable():
    html = render_body([_el("image", data_uri="data:image/png;base64,AAA")])
    assert 'src="data:image/png;base64,AAA"' in html
    assert "data-zoomable" in html
    assert "display:block" in html


def test_centered_image_gets_auto_side_margins():
    html = render_body([_el("image", data_uri="d", alignment="center")])
    assert "margin-left:auto;margin-right:auto" in html


def test_code_carries_its_language():
    html = render_body([_el("code", text="print(1)", language="python")])
    assert html == '<pre><code data-language="python">print(1)</code></pre>'


def test_external_link_opens_in_a_new_tab():
    html = render_body([_el("paragraph", text="docs", link_href="https://example.com")])
    assert '<a href="https://example.com" target="_blank" rel="noopener noreferrer">' in html
    assert ">docs</a>" in html


def test_internal_link_is_tagged_with_its_target_page():
    html = render_body([_el("paragraph", text="Chapter 1", link_target_page=7)])
    assert '<a href="#" data-link-page="7">Chapter 1</a>' in html


def test_children_render_inside_their_parent():
    parent = _el("list_item", text="outer", children=[_el("list_item", text="inner")])
    assert render_body([parent]) == "<li>outer<li>inner</li></li>"


def test_render_page_is_a_standalone_document_containing_the_body():
    response = ParseResponse(
        document=[_el("paragraph", text="hello")],
        metadata=ParseMetadata(
            filename="doc.pdf",
            page_count=1,
            format_detected="pdf",
            parse_duration_ms=5,
            status="success",
        ),
    )
    html = render_page(response)
    assert html.startswith("<!doctype html>")
    assert "<title>doc.pdf</title>" in html
    assert "<p>hello</p>" in html
    assert "</html>" in html
