#!/usr/bin/env -S npx tsx
/**
 * Debug helper: render a parsed document tree to the exact HTML the client produces.
 *
 * Pairs with `services/parser/scripts/parse_file.py` (run via `make parse FILE=...`), which
 * writes `services/parser/.parse-out/<name>.json`. This script reads that JSON and runs it
 * through the real `DocumentRenderer`, writing `<name>.html` alongside it — so you can diff
 * the parser's structured output against the rendered markup from one place. The root
 * `make debug FILE=...` target chains both.
 *
 * Usage (from the repo root):
 *     npx tsx scripts/render-tree.tsx [name]   # name defaults to "sample"
 *
 * `DocumentRenderer` is imported by relative path on purpose: `tsx` does not resolve the
 * `@/` tsconfig alias, and the render chain's only `@/` imports are `import type` (erased
 * at transpile), so no alias resolution is needed at runtime.
 */
import { readFileSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { renderToStaticMarkup } from 'react-dom/server';
import { DocumentRenderer } from '../src/components/reader/document/document-renderer';
import type { ParseResponse } from '../src/types/document-element';

const name = process.argv[2] ?? 'sample';
const outDir = resolve(__dirname, '../services/parser/.parse-out');
const jsonPath = resolve(outDir, `${name}.json`);
const htmlPath = resolve(outDir, `${name}.html`);

const parsed = JSON.parse(readFileSync(jsonPath, 'utf8')) as ParseResponse;
const html = renderToStaticMarkup(<DocumentRenderer tree={parsed.document} />);

writeFileSync(htmlPath, html);
console.log(`wrote ${htmlPath} (${parsed.document.length} top-level elements)`);
