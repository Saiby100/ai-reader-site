import { NextResponse } from 'next/server';

export const runtime = 'nodejs';

const PARSER_URL = process.env.PARSER_SERVICE_URL ?? 'http://localhost:8000';

type ParserCapabilities = {
  /** File extensions the parser service can handle, e.g. ['.pdf', '.docx'] */
  allowedExtensions: string[];
  /** Maximum upload size the parser service accepts, in megabytes */
  maxFileSizeMb: number;
};

export const GET = async () => {
  let response: Response;
  try {
    response = await fetch(`${PARSER_URL}/capabilities`, {
      signal: AbortSignal.timeout(10_000),
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return NextResponse.json(
      { error: `Parser service unavailable: ${message}` },
      { status: 502 },
    );
  }

  if (!response.ok) {
    const body = await response.text();
    return NextResponse.json(
      { error: `Parser error: ${body}` },
      { status: response.status },
    );
  }

  const data = await response.json();
  const capabilities: ParserCapabilities = {
    allowedExtensions: data.allowed_extensions ?? [],
    maxFileSizeMb: data.max_file_size_mb ?? 0,
  };

  return NextResponse.json(capabilities);
};
