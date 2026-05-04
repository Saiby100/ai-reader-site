'use client';

import { useState, useEffect, useCallback } from 'react';
import type { ReaderDocument } from '@/types/document';
import type { DocumentMetadataInput } from '@/types/document-metadata';
import { loadDocument, saveDocument } from '@/lib/reader-storage';
import { saveDocumentMetadataAction } from '@/actions/document-metadata-actions';
import { parseFileToHtml } from '@/lib/file-parsers';

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

const readFileAsText = (file: File): Promise<string> => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsText(file);
  });
};

export const useDocumentUpload = () => {
  const uploadDocument = useCallback(
    async (file: File, metadata: DocumentMetadataInput): Promise<ReaderDocument> => {
      const content = await readFileAsText(file);
      const htmlContent = parseFileToHtml(file.name, content);

      const doc = await saveDocument({ title: metadata.title, author: metadata.author, htmlContent });
      await saveDocumentMetadataAction(doc.id, metadata);

      return doc;
    },
    []
  );

  const uploadFromText = useCallback(
    async (text: string, metadata: DocumentMetadataInput): Promise<ReaderDocument> => {
      const htmlContent = `<pre>${text}</pre>`;

      const doc = await saveDocument({ title: metadata.title, author: metadata.author, htmlContent });
      await saveDocumentMetadataAction(doc.id, metadata);

      return doc;
    },
    []
  );

  return { uploadDocument, uploadFromText };
};