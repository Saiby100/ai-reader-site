'use server';

import type { Note, NoteInput } from '@/types/note';
import { fetchNotesByDocument, insertNote, deleteNote } from '@/lib/notes-db';

export const fetchNotesAction = async (documentId: string): Promise<Note[]> => {
  return fetchNotesByDocument(documentId);
};

export const createNoteAction = async (
  documentId: string,
  input: NoteInput
): Promise<Note> => {
  return insertNote(documentId, input);
};

export const deleteNoteAction = async (id: string): Promise<void> => {
  await deleteNote(id);
};