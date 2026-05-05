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
      <div className="flex flex-1 flex-col gap-2 overflow-y-auto p-3.5">
        <div className="text-[11px] text-ink-3 mb-2 tracking-[0.06em] uppercase font-medium">
          {isLoading ? 'Loading…' : `${notes.length} annotations`}
        </div>
        {!isLoading && notes.length === 0 && (
          <div className="text-center text-ink-3 text-[12.5px] py-8">No notes yet.</div>
        )}
        {notes.map((note) => (
          <NoteCard key={note.id} note={note} onDelete={deleteNote} />
        ))}
      </div>
      <NoteForm onSubmit={createNote} />
    </div>
  );
};