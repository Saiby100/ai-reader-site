export type ReaderDocument = {
  /** Unique identifier (UUID v4) */
  id: string;
  /** Document title displayed at the top of the reader */
  title: string;
  /** Document author displayed below the title */
  author: string;
  /** Normalized HTML string representing the full document content */
  htmlContent: string;
};
