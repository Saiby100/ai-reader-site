import type { DocumentMetadata, DocumentMetadataInput, Stamp } from '@/types/document-metadata';
import { MOCK_USER } from '@/lib/mock-user';

const STORAGE_PREFIX = 'document-metadata:';
const INDEX_KEY = 'document-metadata-ids';

type SerializedStamp = {
  user: { id: string; name: string };
  timestamp: string;
};

type SerializedDocumentMetadata = Omit<DocumentMetadata, 'createdStamp' | 'updatedStamp' | 'viewedStamp'> & {
  createdStamp: SerializedStamp;
  updatedStamp: SerializedStamp;
  viewedStamp: SerializedStamp | null;
};

const createStamp = (): Stamp => ({
  user: { id: MOCK_USER.id, name: MOCK_USER.name },
  timestamp: new Date(),
});

const serializeMetadata = (metadata: DocumentMetadata): string => {
  const serialized: SerializedDocumentMetadata = {
    ...metadata,
    createdStamp: { ...metadata.createdStamp, timestamp: metadata.createdStamp.timestamp.toISOString() },
    updatedStamp: { ...metadata.updatedStamp, timestamp: metadata.updatedStamp.timestamp.toISOString() },
    viewedStamp: metadata.viewedStamp
      ? { ...metadata.viewedStamp, timestamp: metadata.viewedStamp.timestamp.toISOString() }
      : null,
  };
  return JSON.stringify(serialized);
};

const deserializeMetadata = (json: string): DocumentMetadata => {
  const parsed: SerializedDocumentMetadata = JSON.parse(json);
  return {
    ...parsed,
    createdStamp: { ...parsed.createdStamp, timestamp: new Date(parsed.createdStamp.timestamp) },
    updatedStamp: { ...parsed.updatedStamp, timestamp: new Date(parsed.updatedStamp.timestamp) },
    viewedStamp: parsed.viewedStamp
      ? { ...parsed.viewedStamp, timestamp: new Date(parsed.viewedStamp.timestamp) }
      : null,
  };
};

const getIds = (): string[] => {
  const raw = localStorage.getItem(INDEX_KEY);
  return raw ? JSON.parse(raw) : [];
};

const saveIds = (ids: string[]): void => {
  localStorage.setItem(INDEX_KEY, JSON.stringify(ids));
};

// MongoDB equivalent: db.documents.insertOne({ _id: id, ...input, createdAt, updatedAt, viewedAt: null })
export const saveDocumentMetadata = async (
  id: string,
  input: DocumentMetadataInput
): Promise<DocumentMetadata> => {
  const now = createStamp();
  const metadata: DocumentMetadata = {
    id,
    title: input.title,
    author: input.author,
    tags: input.tags,
    createdStamp: now,
    updatedStamp: now,
    viewedStamp: null,
  };

  localStorage.setItem(`${STORAGE_PREFIX}${id}`, serializeMetadata(metadata));

  const ids = getIds();
  if (!ids.includes(id)) {
    ids.push(id);
    saveIds(ids);
  }

  return metadata;
};

// MongoDB equivalent: db.documents.findOne({ _id: id })
export const getDocumentMetadata = async (id: string): Promise<DocumentMetadata | null> => {
  const raw = localStorage.getItem(`${STORAGE_PREFIX}${id}`);
  return raw ? deserializeMetadata(raw) : null;
};

// MongoDB equivalent: db.documents.find({}).toArray()
export const listDocumentMetadata = async (): Promise<DocumentMetadata[]> => {
  const ids = getIds();
  return ids
    .map((id) => {
      const raw = localStorage.getItem(`${STORAGE_PREFIX}${id}`);
      return raw ? deserializeMetadata(raw) : null;
    })
    .filter((doc): doc is DocumentMetadata => doc !== null);
};

// MongoDB equivalent: db.documents.updateOne({ _id: id }, { $set: { ...partial, updatedAt: now } })
export const updateDocumentMetadata = async (
  id: string,
  partial: Partial<DocumentMetadataInput>
): Promise<DocumentMetadata | null> => {
  const existing = await getDocumentMetadata(id);
  if (!existing) return null;

  const updated: DocumentMetadata = {
    ...existing,
    ...partial,
    updatedStamp: createStamp(),
  };

  localStorage.setItem(`${STORAGE_PREFIX}${id}`, serializeMetadata(updated));
  return updated;
};

// MongoDB equivalent: db.documents.updateOne({ _id: id }, { $set: { viewedAt: now } })
export const markDocumentViewed = async (id: string): Promise<DocumentMetadata | null> => {
  const existing = await getDocumentMetadata(id);
  if (!existing) return null;

  const updated: DocumentMetadata = {
    ...existing,
    viewedStamp: createStamp(),
  };

  localStorage.setItem(`${STORAGE_PREFIX}${id}`, serializeMetadata(updated));
  return updated;
};

// MongoDB equivalent: db.documents.deleteOne({ _id: id })
export const deleteDocumentMetadata = async (id: string): Promise<void> => {
  localStorage.removeItem(`${STORAGE_PREFIX}${id}`);
  const ids = getIds().filter((existingId) => existingId !== id);
  saveIds(ids);
};
