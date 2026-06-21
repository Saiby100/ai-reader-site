import { NextResponse } from 'next/server';

export const runtime = 'nodejs';
export const maxDuration = 300;

const PARSER_URL = process.env.PARSER_SERVICE_URL ?? 'http://localhost:8000';
const PARSER_SECRET = process.env.PARSER_SERVICE_SECRET ?? '';

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

  // Pass the parser's structured response straight through; the client renders it
  // into React nodes via the renderer registry.
  const result = await parseResponse.json();

  return NextResponse.json(result);
};
