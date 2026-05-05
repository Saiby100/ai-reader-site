'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import type { Note } from '@/types/note';
import { NOTE_COLORS } from '@/lib/note-colors';

type NoteCardProps = {
  /** The note to display */
  note: Note;
  /** Callback when the note is deleted */
  onDelete: (id: string) => void;
};

const TrashIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
    <path d="M4 6h12M8 6V4h4v2M6 6v10h8V6" />
  </svg>
);

const formatRelativeTime = (date: Date | string): string => {
  const now = Date.now();
  const then = new Date(date).getTime();
  const seconds = Math.floor((now - then) / 1000);

  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}d ago`;
  const months = Math.floor(days / 30);
  return `${months}mo ago`;
};

export const NoteCard = ({ note, onDelete }: NoteCardProps) => {
  const [confirming, setConfirming] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleDelete = useCallback(() => {
    if (confirming) {
      if (timerRef.current) clearTimeout(timerRef.current);
      onDelete(note.id);
    } else {
      setConfirming(true);
      timerRef.current = setTimeout(() => setConfirming(false), 3000);
    }
  }, [confirming, note.id, onDelete]);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  const colors = NOTE_COLORS[note.color] ?? NOTE_COLORS.amber;

  return (
    <div
      className="rounded-r-[var(--radius-sm)] py-2.5 px-3 mb-2 relative group"
      style={{
        background: colors.bg,
        borderLeft: `3px solid ${colors.border}`,
      }}
    >
      <p className="text-xs leading-[1.55] text-ink font-serif">{note.content}</p>
      <div className="text-[11px] text-ink-3 mt-1.5">
        {formatRelativeTime(note.created.timestamp)}
      </div>
      <button
        onClick={handleDelete}
        className={`absolute top-2 right-2 p-0.5 bg-transparent border-none cursor-pointer transition-opacity ${
          confirming ? 'opacity-100 text-rose' : 'opacity-0 group-hover:opacity-40 hover:!opacity-100 text-ink-2'
        }`}
        title={confirming ? 'Click again to confirm' : 'Delete'}
      >
        <TrashIcon size={13} />
      </button>
    </div>
  );
};