import type { DocumentElement, ParseMetadata } from '@/types/document-element';

export type ReaderDocument = {
  /** Unique identifier (UUID v4) */
  id: string;
  /** Document title displayed at the top of the reader */
  title: string;
  /** Document author displayed below the title */
  author: string;
  /** Parsed document tree rendered by the reader */
  document: DocumentElement[];
  /** Document-level metadata from the parse (status, confidence, page count, …) */
  metadata: ParseMetadata;
};
