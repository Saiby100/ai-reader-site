# Document Parser

A FastAPI service that turns a PDF (or DOCX, PPTX, HTML, Markdown, plain text) into a
structured document tree — headings, tables, figures, formulas and links preserved — using
[Docling](https://github.com/docling-project/docling). Clients get JSON; the service also
renders that JSON to standalone HTML so a parse can be checked in a browser.

```
client ──▶ POST /parse ──▶ Docling pipeline ──▶ ParseResponse (JSON tree)
                                                     │
                                       render_html ──┴──▶ out/<name>.html
```

## Requirements

- Python 3.11

## Quick start

```bash
make install          # creates .venv, installs the package with dev extras
make dev              # uvicorn on http://localhost:8000 with auto-reload
```

The first parse downloads the Docling models — a few minutes, once.

### Seeing a parse render

The point of the harness: parse a file and open the result.

```bash
make debug FILE=path/to/document.pdf
# → out/document.json   the full ParseResponse
# → out/document.html   a standalone page — open it in a browser
open out/document.html
```

The HTML is self-contained (inline styles, inline image data URIs, no build step). Images
zoom on click and in-document page links scroll, so what you see matches how a reader
client would present the tree.

### With Docker instead

```bash
docker compose up --build     # http://localhost:8000
```

Compose caches the Docling models in a named volume, so only the first start is slow. The
container is given a 4 GB memory limit; model inference will fail below roughly that.

## Endpoints

| Endpoint | Auth | Returns |
| --- | --- | --- |
| `GET /health` | none | Liveness plus whether models are loaded |
| `GET /capabilities` | none | Allowed extensions and max upload size |
| `POST /parse` | `Bearer $SERVICE_SECRET` | `ParseResponse` — the document tree, metadata, errors |

## Environment

`.env` at the repo root — see `app/config.py` for the full list and the reasoning behind
each default. The ones you are most likely to change:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SERVICE_SECRET` | — | Bearer token callers must present to `/parse` |
| `MAX_FILE_SIZE_MB` | `100` | Upload cap |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx,.pptx,.html,.htm,.md,.txt` | Accepted formats |
| `DO_OCR` | `false` | Turn on for scanned/image-only PDFs |
| `ENABLE_ENRICHMENT` | `false` | Formula/code vision model — accurate but very heavy on CPU |
| `ACCELERATOR_DEVICE` | `auto` | `auto` / `cpu` / `cuda` / `mps` |

Unknown keys are rejected at startup, so keep `.env` to parser settings only.

## Commands

```bash
make install           # create .venv and install with dev extras
make dev               # service with auto-reload
make start             # service without reload
make test              # pytest
make debug FILE=…      # parse a file to out/<name>.{json,html}
make clean             # drop out/
```

## Layout

```
app/
  main.py         FastAPI app — routes, auth, upload validation
  parser.py       all Docling work: conversion, tree building, PDF links, ligature repair
  models.py       the wire contract (pydantic)
  render_html.py  tree → standalone HTML
  config.py       settings
scripts/parse_file.py   the debug CLI behind `make debug`
tests/                  pytest
```

## The contract

`app/models.py` defines a flat, ordered tree of `title` / `heading` / `paragraph` /
`list_item` / `table` / `image` / `code` / `formula` / `caption` nodes. Every node carries
its Docling `ref`, source page and label, so features like citations and click-to-source
can address it later. Nothing Docling-specific — no bounding boxes, no raw provenance —
crosses the boundary. Field names are snake_case on the wire.

`app/render_html.py` maps each element type to its markup through a registry, and asserts
at import that every member of `ElementType` has a renderer — adding a type without one
fails immediately. Each element renders to a real DOM node carrying its `data-ref`, so a
client can address elements in the rendered output too.

## Notable parser behavior

Some PDFs — re-encoded ebooks especially — embed fonts whose `ft`/`fi`/`fl`/`ff` ligature
glyphs have no real Unicode mapping, so `Often` comes out as `O⟦⟧en` in every reader. The
parser detects this, OCRs a few sample words containing each broken glyph, takes the
majority reading, and substitutes it throughout; glyphs it cannot recognize fall back to
full-page OCR of the affected pages. Born-digital PDFs are left untouched. Controlled by
`OCR_FALLBACK` and the `GLYPH_OCR_*` settings.

PDF link annotations are recovered too: `/URI` annotations become `link_href`, and `/GoTo`
annotations become `link_target_page`, including inside table-of-contents table cells.

## Status

This repo was a Next.js reading app with the parser as a sub-service; it is now the parser
alone. Removed in that refactor: the reader UI, the document library, notes and their
MongoDB storage, IndexedDB document storage, and the Gemini chat endpoint. The React
renderer that used to produce the debug HTML now lives in Python as `app/render_html.py`.

## Tech

Python 3.11 · FastAPI · Docling · pydantic-settings · RapidOCR + pypdfium2 for ligature
recovery.

Conventions for contributors are in `CLAUDE.md`.
