'use client';

import { useState, useEffect } from 'react';
import type { ReaderDocument } from '@/types/document';
import { loadDocument } from '@/lib/reader-storage';

export const useReaderDocument = (id: string | null) => {
  const [document, setDocument] = useState<ReaderDocument | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!id) {
      setIsLoading(false);
      return;
    }

    loadDocument(id)
      .then(setDocument)
      .finally(() => setIsLoading(false));
  }, [id]);

  return { document, isLoading };
};
