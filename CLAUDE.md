# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this
repository.

## Commands

```bash
make install           # create .venv (python3.11) and install with dev extras
make dev               # uvicorn with auto-reload on :8000
make start             # uvicorn without reload
make test              # pytest
make debug FILE=…      # parse a file to out/<name>.{json,html}
make clean             # drop out/
```

All targets use `.venv/bin/…` directly — there is no need to activate the venv.

## Architecture

A single FastAPI service wrapping [Docling](https://github.com/docling-project/docling). It
converts uploaded documents into a structured tree and returns it as JSON; it also renders
that tree to standalone HTML for debugging.

```
app/
  main.py         app assembly only — logging, lifespan (model load), `app = FastAPI(…)`,
                  error handlers, `include_router(api_router)`
  logging.py      `configure_logging()` — the one `logging.basicConfig` call
  api/
    router.py     `api_router` — the single place every endpoint is registered
    deps.py       `verify_auth` (bearer) and `validate_upload` (extension / size)
    errors.py     HTTPException → `{"error": …}` JSON, via `register_error_handlers(app)`
    routes/
      health.py         GET  /health
      capabilities.py   GET  /capabilities
      parse.py          POST /parse — parse_document runs in a thread (it is CPU-bound)
  parser.py       all Docling work: converter setup, tree building, PDF link extraction,
                  ligature/PUA recovery. `parse_document(bytes, filename)` is the only
                  entry point; everything else is a `_`-prefixed helper.
  models.py       the wire contract (pydantic) — ParseResponse / DocumentElement / …
  render_html.py  document tree → standalone HTML
  config.py       pydantic-settings `Settings`, exported as the module-level `settings`
scripts/parse_file.py   the debug CLI behind `make debug`
tests/                  pytest
```

### Key patterns

- **One file per endpoint.** Each module in `app/api/routes/` owns an `APIRouter` and
  declares its own method/path decorator, so the verb, path, dependencies and response model
  sit next to the handler. `app/api/router.py` is the central assembly file: adding an
  endpoint means a new route file plus one `include_router` line. `main.py` never grows.
- **One entry point per module boundary.** Nothing Docling-specific leaks past
  `parser.py` — no bounding boxes, no provenance objects. `models.py` is the boundary.
- **Settings are read once.** Import `settings` from `app.config`; never call `Settings()`
  again. Unknown keys in `.env` are rejected at startup.
- **Lazy heavy objects.** The converter and OCR engines are module-level globals built on
  first use (`load_models`, `_get_ocr_converter`, `_get_ocr_engine`) so importing the
  package stays cheap.
- **Renderer registry.** `render_html.RENDERERS` maps every `ElementType` to a function; a
  module-level assert against `get_args(ElementType)` makes a missing renderer an import
  error. Add a type to `ElementType` → add a renderer.
- **Escaping in the renderer.** Text, attributes and code are `html.escape`d; table `html`
  and image `data_uri` are already markup/URI and pass through verbatim.

## Code Style

- Small, focused modules. Group closely related functions in the same file rather than
  splitting one function per file.
- `from __future__ import annotations` at the top of every module.
- Full type hints on every function signature; no bare `dict`/`list` returns where a
  concrete type is known.
- Private helpers are `_`-prefixed and defined below the public functions that use them.
- 4-space indent, double quotes, 100-column lines.
- Comments explain *why*, not *what* — the Docling workarounds especially. Keep the
  existing explanatory comments when refactoring around them.

## Type Definition Guidelines

- **Pydantic models for anything on the wire.** Plain dataclasses/tuples are fine for
  internals.
- **Document every field**: each field in a pydantic model gets a docstring line
  (`"""..."""` directly beneath it) describing its purpose.
- **Prefer narrow types**: `Literal[...]` unions over plain `str` for fields with known
  values (see `ElementType`, `accelerator_device`).
- **No bare `Any`**: use `object` or a concrete type.

## Testing

- `tests/test_parser.py` builds hand-rolled fake Docling objects (`_Item`, `_Doc`, `_Prov`,
  …) so unit tests run without loading models. Extend those fakes rather than importing
  Docling in tests.
- `tests/test_render_html.py` builds `DocumentElement`s directly and asserts on the exact
  markup string.
- Endpoint tests use FastAPI's `TestClient`. Note that importing `app.main` constructs
  `Settings`, so the repo-root `.env` must contain only parser keys.

## Commit Guidelines

- **One commit per task**: separate tasks must be committed separately — never bundle
  unrelated changes into a single commit. If you completed multiple tasks before
  committing, create one commit per task.
- **Ask when unsure**: if it's unclear whether changes belong in one commit or multiple,
  ask before committing.

## IMPORTANT: Always Clarify Before Acting

**Do NOT assume requirements. Always ask questions first.**

Before starting any task — especially feature work, refactors, or anything with ambiguity —
ask clarifying questions to fully understand what is expected. Do not guess at intent,
scope, or implementation details. It is always better to ask one too many questions than to
build the wrong thing.

## Maintaining this file

When making changes that affect architecture, commands, key patterns, or project structure,
update the relevant sections of this CLAUDE.md to keep it accurate.
