"""Render a parsed document tree to standalone HTML.

This is the debug/preview counterpart to the JSON wire format: it turns a
:class:`~app.models.ParseResponse` into a single self-contained HTML file that opens
directly in a browser, so a parse can be eyeballed without any client application.

Two levels are exposed. :func:`render_body` emits just the element markup — every element
becomes a real DOM node carrying its ``data-ref`` and ``data-page``, so downstream features
(citations, click-to-source, highlighting) can address it. :func:`render_page` wraps that in
a full document with reader styling and a small amount of script for image zoom and
in-document page links.
"""

from __future__ import annotations

import html
from typing import Callable, get_args

from .models import DocumentElement, ElementType, ParseResponse

# --- attribute / wrapper helpers -------------------------------------------------


def _attrs(pairs: dict[str, object]) -> str:
    """Serialize attributes, skipping ``None``, with values escaped as HTML attributes."""
    out = []
    for name, value in pairs.items():
        if value is None:
            continue
        out.append(f' {name}="{html.escape(str(value), quote=True)}"')
    return "".join(out)


def _ref_attrs(el: DocumentElement, style: str | None = None) -> str:
    """Reference metadata attached to the rendered DOM node, for later interactivity.

    ``style`` is merged with the alignment rule rather than replacing it, so an element
    that carries both (an aligned image) keeps them.
    """
    rules = [style] if style else []
    if el.alignment:
        rules.append(f"text-align:{el.alignment}")
    return _attrs(
        {
            "data-ref": el.ref,
            "data-page": el.page,
            "style": ";".join(rules) or None,
        }
    )


def _image_style(el: DocumentElement) -> str:
    """Layout style for an image.

    Every image is ``display:block`` so it (a) carries the vertical margin that keeps
    surrounding text off its top/bottom edges, and (b) can be horizontally aligned with auto
    margins — ``text-align`` does nothing on an inline ``<img>``, and vertical margins have
    no effect on inline boxes.
    """
    base = "display:block;margin-top:1.5rem;margin-bottom:1.5rem"
    if el.alignment == "center":
        return f"{base};margin-left:auto;margin-right:auto"
    if el.alignment == "right":
        return f"{base};margin-left:auto"
    return base


def _link_wrap(el: DocumentElement, content: str) -> str:
    """Wrap an element's text in an anchor when it carries a link.

    External links (``link_href``) open in a new tab; internal page-jumps
    (``link_target_page``) render an anchor tagged with ``data-link-page``, which the page
    script intercepts to scroll to that page.
    """
    if el.link_href:
        href = html.escape(el.link_href, quote=True)
        return f'<a href="{href}" target="_blank" rel="noopener noreferrer">{content}</a>'
    if el.link_target_page is not None:
        return f'<a href="#" data-link-page="{el.link_target_page}">{content}</a>'
    return content


def _text(el: DocumentElement) -> str:
    """Escaped text content, linked when the element carries a link."""
    return _link_wrap(el, html.escape(el.text or ""))


# --- per-type renderers ----------------------------------------------------------


def _render_title(el: DocumentElement, children: str) -> str:
    return f"<h1{_ref_attrs(el)}>{_text(el)}</h1>"


def _render_heading(el: DocumentElement, children: str) -> str:
    level = min(max(el.level or 1, 1), 6)
    return f"<h{level}{_ref_attrs(el)}>{_text(el)}</h{level}>"


def _render_paragraph(el: DocumentElement, children: str) -> str:
    return f"<p{_ref_attrs(el)}>{_text(el)}</p>"


def _render_list_item(el: DocumentElement, children: str) -> str:
    return f"<li{_ref_attrs(el)}>{_text(el)}{children}</li>"


def _render_table(el: DocumentElement, children: str) -> str:
    # Docling already exports the table as markup, so it is emitted verbatim.
    return f"<div{_ref_attrs(el)}>{el.html or ''}</div>"


def _render_image(el: DocumentElement, children: str) -> str:
    src = html.escape(el.data_uri or "", quote=True)
    return f'<img{_ref_attrs(el, _image_style(el))} src="{src}" alt="" data-zoomable>'


def _render_code(el: DocumentElement, children: str) -> str:
    lang = _attrs({"data-language": el.language})
    return f"<pre{_ref_attrs(el)}><code{lang}>{html.escape(el.text or '')}</code></pre>"


def _render_formula(el: DocumentElement, children: str) -> str:
    # Rendered as raw LaTeX for now; a later feature can swap in KaTeX off `data-ref`.
    return f"<span{_ref_attrs(el)} data-formula>{html.escape(el.text or '')}</span>"


def _render_caption(el: DocumentElement, children: str) -> str:
    return f"<figcaption{_ref_attrs(el)}>{_text(el)}</figcaption>"


#: Registry mapping each element ``type`` to its renderer. ``children`` is the
#: already-rendered subtree (for elements that nest, e.g. list items); most renderers
#: ignore it.
RENDERERS: dict[ElementType, Callable[[DocumentElement, str], str]] = {
    "title": _render_title,
    "heading": _render_heading,
    "paragraph": _render_paragraph,
    "list_item": _render_list_item,
    "table": _render_table,
    "image": _render_image,
    "code": _render_code,
    "formula": _render_formula,
    "caption": _render_caption,
}

# Adding an element type to `ElementType` without a renderer fails at import, the runtime
# equivalent of the client registry's compile-time exhaustiveness check.
assert set(RENDERERS) == set(get_args(ElementType)), (
    f"renderers missing for: {set(get_args(ElementType)) - set(RENDERERS)}"
)


# --- entry points ----------------------------------------------------------------


def _render_element(el: DocumentElement) -> str:
    children = "".join(_render_element(child) for child in el.children)
    return RENDERERS[el.type](el, children)


def render_body(elements: list[DocumentElement]) -> str:
    """Render a document tree to element markup, with no surrounding page chrome."""
    return "".join(_render_element(el) for el in elements)


def render_page(response: ParseResponse) -> str:
    """Render a full parse into a standalone, browser-openable HTML document."""
    title = html.escape(response.metadata.filename)
    return _PAGE.format(title=title, body=render_body(response.document))


# Palette and typography mirror the reader: a centered 860px serif column on sand.
_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=Lora:wght@400;500;600&display=swap" rel="stylesheet">
<style>
:root {{
  --sand: oklch(97% 0.005 60);
  --sand-3: oklch(88% 0.015 65);
  --ink: oklch(20% 0.01 60);
  --ink-3: oklch(58% 0.01 60);
  --amber: oklch(72% 0.16 75);
  --amber-light: oklch(94% 0.06 75);
  --serif: Lora, Georgia, serif;
  --sans: "DM Sans", system-ui, sans-serif;
}}
body {{ margin: 0; background: var(--sand); color: var(--ink); }}
main {{
  max-width: 860px; margin: 0 auto; padding: 3rem 2rem;
  font-family: var(--serif); font-size: 16.5px; line-height: 1.8;
  overflow-wrap: anywhere;
}}
main * {{ max-width: 100%; }}
h1 {{ font-family: var(--serif); font-size: 30px; font-weight: 600; line-height: 1.25; margin: 0 0 0.875rem; }}
h2 {{ font-family: var(--sans); font-size: 14px; font-weight: 600; letter-spacing: 0.01em; margin: 1.75rem 0 0.5rem; }}
h3, h4, h5, h6 {{ font-family: var(--sans); font-size: 13px; font-weight: 600; margin: 1.5rem 0 0.5rem; }}
p {{ margin: 0 0 22px; text-wrap: pretty; }}
li {{ margin-bottom: 0.375rem; }}
blockquote {{
  border-left: 3px solid var(--amber); background: var(--amber-light);
  padding: 0.375rem 0 0.375rem 0.875rem; border-radius: 0 4px 4px 0; margin: 1.25rem 0;
}}
a {{ color: var(--amber); text-decoration: underline; text-underline-offset: 2px; cursor: pointer; }}
img {{ height: auto; width: auto; max-height: 420px; border-radius: 4px; object-fit: contain; cursor: zoom-in; }}
pre {{ white-space: pre-wrap; font-family: ui-monospace, monospace; font-size: 14px; background: rgb(0 0 0 / 4%); padding: 0.75rem; border-radius: 4px; }}
table {{ border-collapse: collapse; margin: 1.5rem 0; font-family: var(--sans); font-size: 14px; }}
th, td {{ border: 1px solid var(--sand-3); padding: 0.375rem 0.625rem; text-align: left; vertical-align: top; }}
th {{ background: rgb(0 0 0 / 3%); font-weight: 600; }}
figcaption {{ font-family: var(--sans); font-size: 13px; color: var(--ink-3); text-align: center; margin: -0.75rem 0 1.5rem; }}
[data-formula] {{ font-family: ui-monospace, monospace; }}
#zoom {{
  position: fixed; inset: 0; display: none; place-items: center;
  background: rgb(0 0 0 / 80%); cursor: zoom-out; z-index: 10;
}}
#zoom img {{ max-width: 92vw; max-height: 92vh; cursor: zoom-out; }}
</style>
</head>
<body>
<main>{body}</main>
<div id="zoom"><img alt=""></div>
<script>
  const zoom = document.getElementById('zoom');
  document.querySelector('main').addEventListener('click', (event) => {{
    const image = event.target.closest('img[data-zoomable]');
    if (image) {{
      zoom.querySelector('img').src = image.src;
      zoom.style.display = 'grid';
      return;
    }}
    const anchor = event.target.closest('a[data-link-page]');
    if (!anchor) return;
    event.preventDefault();
    const page = anchor.getAttribute('data-link-page');
    document
      .querySelector(`[data-page="${{page}}"]`)
      ?.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
  }});
  zoom.addEventListener('click', () => {{ zoom.style.display = 'none'; }});
</script>
</body>
</html>
"""
