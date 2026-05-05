'use client';

import { useState } from 'react';
import type { NoteInput } from '@/types/note';
import { NOTE_COLORS, NOTE_COLOR_NAMES, DEFAULT_NOTE_COLOR } from '@/lib/note-colors';

type NoteFormProps = {
  /** Callback when a new note is submitted */
  onSubmit: (input: NoteInput) => Promise<void>;
};

const PlusIcon = ({ size = 13 }: { size?: number }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round">
    <path d="M10 4v12M4 10h12" />
  </svg>
);

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
    <div className="p-3 border-t border-border bg-sand flex flex-col gap-2">
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Add a note…"
        rows={2}
        className="w-full resize-none rounded-[var(--radius-sm)] border border-border p-2.5 text-[12.5px] font-serif leading-[1.5] bg-white text-ink outline-none placeholder:text-ink-3"
      />
      <div className="flex items-center justify-between">
        <div className="flex gap-1.5">
          {NOTE_COLOR_NAMES.map((name) => (
            <button
              key={name}
              onClick={() => setColor(name)}
              className={`h-5 w-5 rounded-full transition-shadow ${NOTE_COLORS[name].dot} ${
                color === name ? 'ring-2 ring-offset-1 ring-ink-3' : ''
              }`}
              aria-label={`Select ${name} color`}
            />
          ))}
        </div>
        <button
          onClick={handleSubmit}
          disabled={!content.trim() || isSubmitting}
          className="py-[7px] px-3 rounded-[var(--radius-sm)] bg-accent border-none cursor-pointer text-white text-xs font-medium flex items-center gap-1.5 justify-center font-sans disabled:opacity-40 disabled:cursor-not-allowed"
        >
          <PlusIcon size={13} /> {isSubmitting ? 'Saving…' : 'Add Note'}
        </button>
      </div>
    </div>
  );
};