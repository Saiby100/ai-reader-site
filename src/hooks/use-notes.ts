'use client';

import { useCallback, useEffect, useState } from 'react';
import type { Note, NoteInput } from '@/types/note';
import { fetchNotesAction, createNoteAction, deleteNoteAction } from '@/actions/note-actions';

export const useNotes = (documentId: string | null) => {
  const [notes, setNotes] = useState<Note[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!documentId) {
      setNotes([]);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    fetchNotesAction(documentId)
      .then(setNotes)
      .finally(() => setIsLoading(false));
  }, [documentId]);

  const createNote = useCallback(
    async (input: NoteInput) => {
      if (!documentId) return;
      const note = await createNoteAction(documentId, input);
      setNotes((prev) => [...prev, note]);
    },
    [documentId]
  );

  const deleteNote = useCallback(async (id: string) => {
    await deleteNoteAction(id);
    setNotes((prev) => prev.filter((n) => n.id !== id));
  }, []);

  return { notes, isLoading, createNote, deleteNote };
};