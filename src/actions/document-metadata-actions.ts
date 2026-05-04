'use server';

import type { DocumentMetadata, DocumentMetadataInput } from '@/types/document-metadata';
import {
  insertDocumentMetadata,
  markDocumentViewed,
  deleteDocumentMetadata,
} from '@/lib/document-metadata-db';

export const saveDocumentMetadataAction = async (
  id: string,
  input: DocumentMetadataInput
): Promise<DocumentMetadata> => {
  return insertDocumentMetadata(id, input);
};

export const markDocumentViewedAction = async (id: string): Promise<void> => {
  await markDocumentViewed(id);
};

export const deleteDocumentMetadataAction = async (id: string): Promise<void> => {
  await deleteDocumentMetadata(id);
};
