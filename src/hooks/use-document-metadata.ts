'use client';

import { useState, useEffect, useCallback } from 'react';
import type { DocumentMetadata } from '@/types/document-metadata';
import { listDocumentMetadata, markDocumentViewed } from '@/lib/document-metadata-store';

export const useDocumentMetadataLibrary = () => {
  const [metadataList, setMetadataList] = useState<DocumentMetadata[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(() => {
    setIsLoading(true);
    listDocumentMetadata()
      .then(setMetadataList)
      .finally(() => setIsLoading(false));
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return { metadataList, isLoading, refresh };
};

export const useMarkDocumentViewed = () => {
  const markViewed = useCallback(async (id: string) => {
    await markDocumentViewed(id);
  }, []);

  return { markViewed };
};