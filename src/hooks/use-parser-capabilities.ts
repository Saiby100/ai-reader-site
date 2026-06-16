'use client';

import { useEffect, useState } from 'react';

export type ParserCapabilities = {
  /** File extensions the server can parse, e.g. ['.pdf', '.docx'] */
  allowedExtensions: string[];
  /** Maximum upload size the server accepts, in megabytes */
  maxFileSizeMb: number;
};

/**
 * Fetches the server-defined parsing capabilities (supported file types and
 * size limit). The parser service is the single source of truth — the client
 * never hardcodes which formats are accepted.
 */
export const useParserCapabilities = () => {
  const [capabilities, setCapabilities] = useState<ParserCapabilities | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    fetch('/api/parse/capabilities')
      .then(async (res) => {
        if (!res.ok) throw new Error('Document service unavailable');
        return res.json() as Promise<ParserCapabilities>;
      })
      .then((data) => {
        if (!active) return;
        setCapabilities(data);
        setError(null);
      })
      .catch((err) => {
        if (!active) return;
        setCapabilities(null);
        setError(err instanceof Error ? err.message : 'Document service unavailable');
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { capabilities, isLoading, error };
};
