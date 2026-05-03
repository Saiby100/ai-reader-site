'use client';

import { useState, useEffect, useCallback } from 'react';
import type { ReaderDocument } from '@/types/document';
import { loadDocument, listDocuments, saveDocument } from '@/lib/reader-storage';
import { parseFileToHtml, getFileExtension } from '@/lib/file-parsers';

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

export const useDocumentLibrary = () => {
  const [documents, setDocuments] = useState<ReaderDocument[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(() => {
    setIsLoading(true);
    listDocuments()
      .then(setDocuments)
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { documents, isLoading, refresh };
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
  const uploadDocument = useCallback(async (file: File): Promise<ReaderDocument> => {
    const content = await readFileAsText(file);
    const ext = getFileExtension(file.name);
    const title = file.name.replace(new RegExp(`\\${ext}$`, 'i'), '');
    const htmlContent = parseFileToHtml(file.name, content);

    return saveDocument({ title, author: '', htmlContent });
  }, []);

  return { uploadDocument };
};
