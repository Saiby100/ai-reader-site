# AI Reader

A reading app for long, complex documents. Upload a PDF (or DOCX, PPTX, HTML, Markdown,
plain text), and it is parsed into a structured document tree and rendered as clean,
readable HTML — headings, tables, figures, formulas and links preserved — with a side
panel for notes taken while you read.

The parse is done by a separate Python service built on
[Docling](https://github.com/docling-project/docling); the Next.js app never touches the
raw file format.

```
browser ──▶ Next.js (/api/parse) ──▶ parser service (FastAPI + Docling)
   │                                          │
   │        ParseResponse (JSON tree) ◀────────┘
   ▼
IndexedDB (document tree)      MongoDB (metadata + notes)
```

## Requirements

- Node.js 20+
- Python 3.11 (parser service)
- MongoDB (local or Atlas) — stores document metadata and notes
- A Google Generative AI API key, for the chat endpoint

## Quick start

Two processes: the parser service and the web app.

```bash
# 1. Parser service (first run downloads Docling models — a few minutes)
cd services/parser
make install          # creates .venv, installs the package with dev extras
make dev              # uvicorn on http://localhost:8000

# 2. Web app (repo root, separate terminal)
npm install
npm run dev           # http://localhost:3000
```

Open http://localhost:3000, fill in title/author/tags, and drop in a file.

### With Docker instead

```bash
docker compose up --build     # web on :3000, parser internal on :8000
```

Compose sets a shared `dev-secret` for the two services and caches the Docling models in a
named volume, so only the first start is slow. The parser is given a 4 GB memory limit;
model inference will fail below roughly that.

## Environment

Root `.env`:

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `MONGODB_URI` | yes | — | Connection string for metadata and notes |
| `MONGODB_DB_NAME` | no | `ai-reader` | Database name |
| `PARSER_SERVICE_URL` | no | `http://localhost:8000` | Where the parser service lives |
| `PARSER_SERVICE_SECRET` | yes | — | Must match the parser's `SERVICE_SECRET` |
| `GOOGLE_GENERATIVE_AI_API_KEY` | yes | — | Used by `/api/chat` (Gemini via the AI SDK) |

`services/parser/.env` — see `services/parser/app/config.py` for the full list and the
reasoning behind each default. The ones you are most likely to change:

| Variable | Default | Purpose |
| --- | --- | --- |
| `SERVICE_SECRET` | — | Bearer token the web app must present to `/parse` |
| `MAX_FILE_SIZE_MB` | `100` | Upload cap |
| `ALLOWED_EXTENSIONS` | `.pdf,.docx,.pptx,.html,.htm,.md,.txt` | Accepted formats |
| `DO_OCR` | `false` | Turn on for scanned/image-only PDFs |
| `ENABLE_ENRICHMENT` | `false` | Formula/code vision model — accurate but very heavy on CPU |
| `ACCELERATOR_DEVICE` | `auto` | `auto` / `cpu` / `cuda` / `mps` |

## Commands

```bash
npm run dev            # Next.js dev server
npm run build          # production build (standalone output)
npm run start          # serve the production build
npm run lint           # ESLint

cd services/parser
make dev               # parser with auto-reload
make start             # parser without reload
make test              # pytest
```

### Parser debugging harness

Parse a file straight to JSON, then render that JSON through the *real* client renderer, so
the structured tree and the resulting markup can be diffed side by side:

```bash
make debug FILE=path/to/document.pdf
# → services/parser/.parse-out/document.json
# → services/parser/.parse-out/document.html
```

`make parse FILE=…` and `make render NAME=…` run the two halves separately.

## How it fits together

**Parser service** (`services/parser/`) — FastAPI wrapping Docling.

| Endpoint | Auth | Returns |
| --- | --- | --- |
| `GET /health` | none | Liveness plus whether models are loaded |
| `GET /capabilities` | none | Allowed extensions and max upload size |
| `POST /parse` | `Bearer $SERVICE_SECRET` | `ParseResponse` — the document tree, metadata, errors |

It owns the *only* translation from Docling's model into the app's wire format. Nothing
Docling-specific — no bounding boxes, no raw provenance — crosses the boundary.

**The contract** (`src/types/document-element.ts` ↔ `services/parser/app/models.py`) — a
flat, ordered tree of `title` / `heading` / `paragraph` / `list_item` / `table` / `image` /
`code` / `formula` / `caption` nodes. Every node carries its Docling `ref`, source page and
label, so features like citations and click-to-source can address it later. The wire format
is snake_case on both sides, so there is no field transform anywhere.

**Renderer** (`src/components/reader/document/`) — a registry mapping each element type to a
React renderer. The registry type is derived from the `DocumentElement` union, so adding an
element type without a renderer is a compile error.

**Storage** — parsed document trees live in the browser's IndexedDB (`src/lib/reader-storage.ts`);
metadata and notes live in MongoDB, written through server actions in `src/actions/`.

### Notable parser behavior

Some PDFs — re-encoded ebooks especially — embed fonts whose `ft`/`fi`/`fl`/`ff` ligature
glyphs have no real Unicode mapping, so `Often` comes out as `O⟦⟧en` in every reader. The
parser detects this, OCRs a few sample words containing each broken glyph, takes the
majority reading, and substitutes it throughout; glyphs it cannot recognize fall back to
full-page OCR of the affected pages. Born-digital PDFs are left untouched. Controlled by
`OCR_FALLBACK` and the `GLYPH_OCR_*` settings.

## Status

Works today: upload and parse, the reader with reading-progress and image lightbox, the
document library with tags and filtering, and notes.

Not yet wired up: the Q&A, Discussion and Ask AI tabs in the reader drawer are placeholders.
`/api/chat` exists and streams from Gemini given a reading context, but no UI calls it yet.
Auth is a hardcoded user in `src/lib/mock-user.ts`.

## Tech

Next.js 16 (App Router) · React 19 · TypeScript strict · Tailwind CSS v4 · Vercel AI SDK
with the Google provider · MongoDB · FastAPI + Docling.

Conventions for contributors are in `CLAUDE.md`.
