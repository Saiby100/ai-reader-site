import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 300;

const PARSER_URL = process.env.PARSER_SERVICE_URL ?? 'http://localhost:8000';
const PARSER_SECRET = process.env.PARSER_SERVICE_SECRET ?? '';
const MAX_FILE_SIZE = 100 * 1024 * 1024;
const ALLOWED_EXTENSIONS = new Set([
  '.pdf', '.docx', '.pptx', '.html', '.htm', '.md', '.txt',
]);

export const POST = async (request: Request) => {
  const formData = await request.formData();
  const file = formData.get('file');

  if (!(file instanceof File)) {
    return NextResponse.json({ error: 'No file provided' }, { status: 400 });
  }

  const ext = getExtension(file.name);
  if (!ALLOWED_EXTENSIONS.has(ext)) {
    return NextResponse.json(
      { error: `Unsupported file type: ${ext}` },
      { status: 415 },
    );
  }

  if (file.size > MAX_FILE_SIZE) {
    return NextResponse.json({ error: 'File too large' }, { status: 413 });
  }

  const outForm = new FormData();
  outForm.append('file', file, file.name);

  let parseResponse: Response;
  try {
    parseResponse = await fetch(`${PARSER_URL}/parse/stream`, {
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

  return new Response(parseResponse.body, {
    headers: {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      Connection: 'keep-alive',
    },
  });
};

const getExtension = (filename: string): string => {
  const dot = filename.lastIndexOf('.');
  return dot === -1 ? '' : filename.slice(dot).toLowerCase();
};
