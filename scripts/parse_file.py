#!/usr/bin/env python3
"""Parse a single document to JSON and standalone HTML, then exit.

Loads the (slow) Docling models, parses the file at the given path via
``app.parsing.parse_document``, prints a short summary, and writes both the full
``ParseResponse`` JSON and a browser-openable HTML rendering of it to ``out/`` at the repo
root. Open the HTML to see how the parse actually renders.

Usage:
    python scripts/parse_file.py path/to/document.pdf

Or via the Makefile, which uses the venv's interpreter:
    make debug FILE=path/to/document.pdf
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `from app...` imports regardless of the current working directory.
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.models import ParseResponse  # noqa: E402
from app.parsing import load_models, parse_document  # noqa: E402
from app.render_html import render_page  # noqa: E402

OUTPUT_DIR = REPO_ROOT / "out"


def _summarize(resp: ParseResponse) -> str:
    counts: dict[str, int] = {}
    for element in resp.document:
        counts[element.type] = counts.get(element.type, 0) + 1
    return ", ".join(f"{k}={v}" for k, v in sorted(counts.items())) or "(no elements)"


def _parse(path: Path, out_dir: Path) -> int:
    if not path.exists():
        print(f"  not found: {path}")
        return 1

    resp = parse_document(path.read_bytes(), path.name)

    json_path = out_dir / f"{path.stem}.json"
    html_path = out_dir / f"{path.stem}.html"
    json_path.write_text(resp.model_dump_json(indent=2))
    html_path.write_text(render_page(resp))

    print(f"  parsed {path.name}: {_summarize(resp)}")
    print(
        f"  {resp.metadata.page_count} page(s), "
        f"{resp.metadata.parse_duration_ms} ms, "
        f"format={resp.metadata.format_detected}"
    )
    for error in resp.errors:
        print(f"  ! {error}")
    print(f"  -> {json_path}")
    print(f"  -> {html_path}")
    return 0


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: python scripts/parse_file.py path/to/document.pdf")
        return 2

    path = Path(sys.argv[1]).expanduser()
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"Output dir: {out_dir}")
    print("Loading Docling models (one-time, slow)...")
    load_models()
    return _parse(path, out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
