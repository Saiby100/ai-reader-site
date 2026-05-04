import type { Stamp } from '@/types/stamp';

/** A user-created note attached to a document */
export type Note = {
  /** UUID v4 identifier */
  id: string;
  /** The text body of the note */
  content: string;
  /** Color name for visual categorization (e.g. 'yellow', 'blue') */
  color: string;
  /** UUID of the document this note belongs to */
  documentId: string;
  /** When and by whom the note was created */
  created: Stamp;
  /** When and by whom the note was last modified */
  updated: Stamp;
};

/** Fields the user provides when creating a new note */
export type NoteInput = {
  /** The text body of the note */
  content: string;
  /** Color name for visual categorization */
  color: string;
};