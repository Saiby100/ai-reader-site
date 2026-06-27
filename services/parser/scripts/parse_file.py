#!/usr/bin/env python3
"""Parse a single document and write its ParseResponse JSON, then exit.

Loads the (slow) Docling models, parses the file at the given path via
``app.parser.parse_document``, prints a short summary, and writes the full
``ParseResponse`` JSON to the ``.parse-out/`` folder (git-ignored) at the parser
root. Pairs with ``scripts/render-tree.tsx`` (run from the repo root), which turns
that JSON into the client's rendered HTML — the root ``make debug`` target chains
both for the same file.

Usage:
    python scripts/parse_file.py [path]

``path`` defaults to the bundled sample fixture (tests/fixtures/sample.docx).
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow `from app...` imports regardless of the current working directory.
PARSER_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PARSER_ROOT))

from app.models import ParseResponse  # noqa: E402
from app.parser import load_models, parse_document  # noqa: E402

DEFAULT_FIXTURE = PARSER_ROOT / "tests" / "fixtures" / "sample.docx"
OUTPUT_DIR = PARSER_ROOT / ".parse-out"


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

    out_path = out_dir / f"{path.stem}.json"
    out_path.write_text(resp.model_dump_json(indent=2))
    print(f"  parsed {path.name}: {_summarize(resp)}")
    print(
        f"  {resp.metadata.page_count} page(s), "
        f"{resp.metadata.parse_duration_ms} ms, "
        f"format={resp.metadata.format_detected}"
    )
    print(f"  -> {out_path}")
    return 0


def main() -> int:
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    path = Path(sys.argv[1]).expanduser() if len(sys.argv) > 1 else DEFAULT_FIXTURE

    print(f"Output dir: {out_dir}")
    print("Loading Docling models (one-time, slow)...")
    load_models()
    return _parse(path, out_dir)


if __name__ == "__main__":
    raise SystemExit(main())
