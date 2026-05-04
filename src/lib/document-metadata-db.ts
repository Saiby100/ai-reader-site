import type { DocumentMetadata, DocumentMetadataInput } from '@/types/document-metadata';
import type { Stamp } from '@/types/stamp';
import { MOCK_USER } from '@/lib/mock-user';
import { getDb } from '@/lib/mongodb';

type DocumentMetadataDoc = DocumentMetadata & { _id: string };

const COLLECTION = 'document-metadata';

const createStamp = (): Stamp => ({
  user: { id: MOCK_USER.id, name: MOCK_USER.name },
  timestamp: new Date(),
});

const docToMetadata = (doc: DocumentMetadataDoc): DocumentMetadata => {
  const { _id, ...rest } = doc;
  void _id;
  return rest;
};

export const fetchDocumentMetadataList = async (userId: string): Promise<DocumentMetadata[]> => {
  const db = await getDb();
  const docs = await db
    .collection<DocumentMetadataDoc>(COLLECTION)
    .find({ 'created.user.id': userId })
    .toArray();
  return docs.map(docToMetadata);
};

export const fetchDocumentMetadata = async (id: string): Promise<DocumentMetadata | null> => {
  const db = await getDb();
  const doc = await db.collection<DocumentMetadataDoc>(COLLECTION).findOne({ _id: id });
  return doc ? docToMetadata(doc) : null;
};

export const insertDocumentMetadata = async (
  id: string,
  input: DocumentMetadataInput
): Promise<DocumentMetadata> => {
  const db = await getDb();
  const now = createStamp();
  const metadata: DocumentMetadata = {
    id,
    title: input.title,
    author: input.author,
    tags: input.tags,
    created: now,
    updated: now,
    viewed: null,
  };
  await db.collection<DocumentMetadataDoc>(COLLECTION).insertOne({ _id: id, ...metadata });
  return metadata;
};

export const updateDocumentMetadata = async (
  id: string,
  partial: Partial<DocumentMetadataInput>
): Promise<DocumentMetadata | null> => {
  const db = await getDb();
  const result = await db.collection<DocumentMetadataDoc>(COLLECTION).findOneAndUpdate(
    { _id: id },
    { $set: { ...partial, updated: createStamp() } },
    { returnDocument: 'after' }
  );
  return result ? docToMetadata(result) : null;
};

export const markDocumentViewed = async (id: string): Promise<DocumentMetadata | null> => {
  const db = await getDb();
  const result = await db.collection<DocumentMetadataDoc>(COLLECTION).findOneAndUpdate(
    { _id: id },
    { $set: { viewed: createStamp() } },
    { returnDocument: 'after' }
  );
  return result ? docToMetadata(result) : null;
};

export const deleteDocumentMetadata = async (id: string): Promise<void> => {
  const db = await getDb();
  await db.collection<DocumentMetadataDoc>(COLLECTION).deleteOne({ _id: id });
};
