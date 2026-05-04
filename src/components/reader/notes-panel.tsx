'use client';

import { useNotes } from '@/hooks/use-notes';
import { NoteCard } from '@/components/reader/note-card';
import { NoteForm } from '@/components/reader/note-form';

type NotesPanelProps = {
  /** Document ID to load notes for */
  documentId: string;
};

export const NotesPanel = ({ documentId }: NotesPanelProps) => {
  const { notes, isLoading, createNote, deleteNote } = useNotes(documentId);

  return (
    <div className="flex flex-1 flex-col overflow-hidden">
      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-3">
        {isLoading && (
          <p className="text-sm text-gray-400">Loading notes...</p>
        )}
        {!isLoading && notes.length === 0 && (
          <p className="text-sm text-gray-400">No notes yet.</p>
        )}
        {notes.map((note) => (
          <NoteCard key={note.id} note={note} onDelete={deleteNote} />
        ))}
      </div>
      <NoteForm onSubmit={createNote} />
    </div>
  );
};