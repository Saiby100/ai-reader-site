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

  const accentColor = NOTE_COLORS[note.color]?.accent ?? 'bg-gray-300';

  return (
    <div className="flex overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700">
      <div className={`w-1 shrink-0 ${accentColor}`} />
      <div className="flex flex-1 flex-col gap-1 p-3">
        <p className="text-sm text-gray-800 dark:text-gray-200">{note.content}</p>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">{formatRelativeTime(note.created.timestamp)}</span>
          <button
            onClick={handleDelete}
            className={`text-xs transition-colors ${
              confirming
                ? 'font-medium text-red-600 dark:text-red-400'
                : 'text-gray-400 hover:text-red-500'
            }`}
          >
            {confirming ? 'Confirm?' : 'Delete'}
          </button>
        </div>
      </div>
    </div>
  );
};