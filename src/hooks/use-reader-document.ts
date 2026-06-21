'use client';

import { useState, useEffect, useCallback } from 'react';
import type { ReaderDocument } from '@/types/document';
import type { DocumentElement, ParseResponse } from '@/types/document-element';
import type { DocumentMetadataInput } from '@/types/document-metadata';
import { loadDocument, saveDocument } from '@/lib/reader-storage';
import { saveDocumentMetadataAction } from '@/actions/document-metadata-actions';

export const useReaderDocument = (id: string | null) => {
  const [document, setDocument] = useState<ReaderDocument | null>(null);
  const [isLoading, setIsLoading] = useState(!!id);

  useEffect(() => {
    if (!id) return;

    setIsLoading(true);
    loadDocument(id)
      .then(setDocument)
      .finally(() => setIsLoading(false));
  }, [id]);

  return { document, isLoading };
};

export const useDocumentUpload = () => {
  const uploadDocument = useCallback(
    async (file: File, metadata: DocumentMetadataInput): Promise<ReaderDocument> => {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/parse', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const err = await response.json().catch(() => ({ error: 'Parse failed' }));
        throw new Error(err.error ?? 'Parse failed');
      }

      const parsed = (await response.json()) as ParseResponse;

      const doc = await saveDocument({
        title: metadata.title,
        author: metadata.author,
        document: parsed.document,
        metadata: parsed.metadata,
      });
      await saveDocumentMetadataAction(doc.id, metadata);

      return doc;
    },
    []
  );

  const uploadFromText = useCallback(
    async (text: string, metadata: DocumentMetadataInput): Promise<ReaderDocument> => {
      // Wrap pasted text in a single preformatted element so stored documents
      // always share the structured-tree shape.
      const document: DocumentElement[] = [{ type: 'code', text }];

      const doc = await saveDocument({
        title: metadata.title,
        author: metadata.author,
        document,
        metadata: {
          filename: metadata.title,
          page_count: 1,
          format_detected: 'txt',
          parse_duration_ms: 0,
          status: 'success',
        },
      });
      await saveDocumentMetadataAction(doc.id, metadata);

      return doc;
    },
    []
  );

  return { uploadDocument, uploadFromText };
};