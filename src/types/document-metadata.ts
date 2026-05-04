import type { Stamp } from '@/types/stamp';

/** Metadata record stored in the document database */
export type DocumentMetadata = {
  /** UUID matching the IndexedDB document key */
  id: string;
  /** User-facing document title */
  title: string;
  /** Document author name */
  author: string;
  /** User-assigned classification tags */
  tags: string[];
  /** When the document was first created/uploaded */
  created: Stamp;
  /** When the metadata was last modified */
  updated: Stamp;
  /** When the document was last opened for reading */
  viewed: Stamp | null;
};

/** Fields the user provides when uploading a new document */
export type DocumentMetadataInput = {
  /** User-facing document title */
  title: string;
  /** Document author name */
  author: string;
  /** User-assigned classification tags */
  tags: string[];
};