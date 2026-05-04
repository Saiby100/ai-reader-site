import type { Note, NoteInput } from '@/types/note';
import type { Stamp } from '@/types/stamp';
import { MOCK_USER } from '@/lib/mock-user';
import { getDb } from '@/lib/mongodb';

type NoteDoc = Note & { _id: string };

const COLLECTION = 'notes';

const createStamp = (): Stamp => ({
  user: { id: MOCK_USER.id, name: MOCK_USER.name },
  timestamp: new Date(),
});

const docToNote = (doc: NoteDoc): Note => {
  const { _id, ...rest } = doc;
  void _id;
  return rest;
};

export const fetchNotesByDocument = async (documentId: string): Promise<Note[]> => {
  const db = await getDb();
  const docs = await db
    .collection<NoteDoc>(COLLECTION)
    .find({ documentId })
    .sort({ 'created.timestamp': 1 })
    .toArray();
  return docs.map(docToNote);
};

export const insertNote = async (documentId: string, input: NoteInput): Promise<Note> => {
  const db = await getDb();
  const now = createStamp();
  const id = crypto.randomUUID();
  const note: Note = {
    id,
    content: input.content,
    color: input.color,
    documentId,
    created: now,
    updated: now,
  };
  await db.collection<NoteDoc>(COLLECTION).insertOne({ _id: id, ...note });
  return note;
};

export const deleteNote = async (id: string): Promise<void> => {
  const db = await getDb();
  await db.collection<NoteDoc>(COLLECTION).deleteOne({ _id: id });
};