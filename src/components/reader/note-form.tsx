'use client';

import { useState } from 'react';
import type { NoteInput } from '@/types/note';
import { NOTE_COLORS, NOTE_COLOR_NAMES, DEFAULT_NOTE_COLOR } from '@/lib/note-colors';

type NoteFormProps = {
  /** Callback when a new note is submitted */
  onSubmit: (input: NoteInput) => Promise<void>;
};

export const NoteForm = ({ onSubmit }: NoteFormProps) => {
  const [content, setContent] = useState('');
  const [color, setColor] = useState(DEFAULT_NOTE_COLOR);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    const trimmed = content.trim();
    if (!trimmed || isSubmitting) return;

    setIsSubmitting(true);
    try {
      await onSubmit({ content: trimmed, color });
      setContent('');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSubmit();
    }
  };

  return (
    <div className="flex flex-col gap-2 border-t border-gray-200 p-3 dark:border-gray-800">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Add a note..."
        rows={3}
        className="w-full resize-none rounded-md border border-gray-200 bg-transparent p-2 text-sm
          text-gray-800 placeholder-gray-400 outline-none focus:border-blue-500
          dark:border-gray-700 dark:text-gray-200 dark:placeholder-gray-500"
      />
      <div className="flex items-center justify-between">
        <div className="flex gap-1.5">
          {NOTE_COLOR_NAMES.map((name) => (
            <button
              key={name}
              onClick={() => setColor(name)}
              className={`h-5 w-5 rounded-full transition-shadow ${NOTE_COLORS[name].dot} ${
                color === name ? 'ring-2 ring-offset-1 ring-gray-500 dark:ring-offset-gray-900' : ''
              }`}
              aria-label={`Select ${name} color`}
            />
          ))}
        </div>
        <button
          onClick={handleSubmit}
          disabled={!content.trim() || isSubmitting}
          className="rounded-md bg-blue-600 px-3 py-1 text-xs font-medium text-white
            transition-opacity hover:bg-blue-700 disabled:opacity-40"
        >
          {isSubmitting ? 'Saving...' : 'Add'}
        </button>
      </div>
    </div>
  );
};