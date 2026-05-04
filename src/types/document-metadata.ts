/** Represents a user action stamp with actor and time */
export type Stamp = {
  /** The user who performed the action */
  user: {
    /** Unique user identifier */
    id: string;
    /** Display name of the user */
    name: string;
  };
  /** When the action occurred */
  timestamp: Date;
};

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
  createdStamp: Stamp;
  /** When the metadata was last modified */
  updatedStamp: Stamp;
  /** When the document was last opened for reading */
  viewedStamp: Stamp | null;
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