#!/usr/bin/env python3
"""Interactive harness for testing the parser in isolation.

Loads the (slow) Docling models once, then runs a long-running prompt loop.
Enter a file path and the document is parsed via ``app.parser.parse_document``;
a summary is printed and the full ``ParseResponse`` JSON is written to the
``.parse-out/`` folder (git-ignored) at the parser root for inspection.

Usage:
    python scripts/parse_repl.py

Commands at the prompt:
    <path>   parse the file at <path>
    <empty>  parse the bundled sample fixture (tests/fixtures/sample.docx)
    q        quit
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


def _handle(path: Path, out_dir: Path) -> None:
    if not path.exists():
        print(f"  not found: {path}")
        return
    try:
        resp = parse_document(path.read_bytes(), path.name)
    except Exception as exc:  # noqa: BLE001 - surface any parse error and keep looping
        print(f"  parse failed: {exc}")
        return

    out_path = out_dir / f"{path.stem}.json"
    out_path.write_text(resp.model_dump_json(indent=2))
    print(f"  parsed {path.name}: {_summarize(resp)}")
    print(
        f"  {resp.metadata.page_count} page(s), "
        f"{resp.metadata.parse_duration_ms} ms, "
        f"format={resp.metadata.format_detected}"
    )
    print(f"  -> {out_path}")


def main() -> None:
    out_dir = OUTPUT_DIR
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"Output dir: {out_dir}")
    print("Loading Docling models (one-time, slow)...")
    load_models()
    print("Ready. Enter a file path to parse, blank for the sample fixture, or 'q' to quit.")

    while True:
        try:
            raw = input("\nfile> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break

        if raw.lower() in {"q", "quit", "exit"}:
            print("Bye.")
            break

        path = Path(raw).expanduser() if raw else DEFAULT_FIXTURE
        _handle(path, out_dir)


if __name__ == "__main__":
    main()
