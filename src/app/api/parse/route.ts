import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 300;

const PARSER_URL = process.env.PARSER_SERVICE_URL ?? 'http://localhost:8000';
const PARSER_SECRET = process.env.PARSER_SERVICE_SECRET ?? '';

type DocumentElement = {
  type: string;
  level?: number | null;
  text?: string | null;
  html?: string | null;
  data_uri?: string | null;
  children?: DocumentElement[];
};

export const POST = async (request: Request) => {
  const formData = await request.formData();
  const file = formData.get('file');

  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 });
  }

  const outForm = new FormData();
  outForm.append('file', file, file.name);

  let parseResponse: Response;
  try {
    parseResponse = await fetch(`${PARSER_URL}/parse`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${PARSER_SECRET}` },
      body: outForm,
      signal: AbortSignal.timeout(290_000),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json(
      { error: `Parser service unavailable: ${message}` },
      { status: 502 },
    );
  }

  if (!parseResponse.ok) {
    const body = await parseResponse.text();
    return NextResponse.json(
      { error: `Parser error: ${body}` },
      { status: parseResponse.status },
    );
  }

  const result = await parseResponse.json();
  const htmlContent = treeToHtml(result.document ?? []);

  return NextResponse.json({
    structured: result,
    htmlContent,
  });
};

const treeToHtml = (elements: DocumentElement[]): string =>
  elements.map(elementToHtml).join('\n');

const elementToHtml = (el: DocumentElement): string => {
  const childHtml = el.children?.length ? treeToHtml(el.children) : '';

  switch (el.type) {
    case 'title':
      return `<h1>${escapeHtml(el.text ?? '')}</h1>`;
    case 'heading': {
      const level = Math.min(Math.max(el.level ?? 1, 1), 6);
      return `<h${level}>${escapeHtml(el.text ?? '')}</h${level}>`;
    }
    case 'paragraph':
      return `<p>${escapeHtml(el.text ?? '')}</p>`;
    case 'table':
      return el.html ?? '';
    case 'image':
      return el.data_uri ? `<img src="${el.data_uri}" alt="" />` : '';
    case 'list':
      return `<ul>${childHtml}</ul>`;
    case 'list_item':
      return `<li>${escapeHtml(el.text ?? '')}${childHtml}</li>`;
    case 'code_block':
      return `<pre><code>${escapeHtml(el.text ?? '')}</code></pre>`;
    case 'page_break':
      return '<hr />';
    default:
      return el.text ? `<p>${escapeHtml(el.text)}</p>` : childHtml;
  }
};

const escapeHtml = (str: string): string =>
  str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
