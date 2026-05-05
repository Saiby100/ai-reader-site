'use client';

import Link from 'next/link';
import { SparkleIcon, SearchIcon, NotesIcon } from '@/components/icons';

type ReaderHeaderProps = {
  /** Document title */
  title: string;
  /** Document author */
  author: string;
  /** Reading progress 0-100 */
  progress: number;
  /** Whether the side drawer is open */
  drawerOpen: boolean;
  /** Callback to toggle the drawer */
  onToggleDrawer: () => void;
};

export const ReaderHeader = ({ title, author, progress, drawerOpen, onToggleDrawer }: ReaderHeaderProps) => {
  return (
    <header className="h-[52px] shrink-0 border-b border-border bg-white flex items-center px-5 gap-3 z-50 relative shadow-[0_1px_0_var(--border)]">
      <Link
        href="/"
        className="flex items-center gap-2 px-1 py-1 rounded-[var(--radius-sm)] transition-colors hover:bg-sand-2 no-underline"
        title="Back to Library"
      >
        <div className="w-[26px] h-[26px] rounded-[var(--radius-sm)] bg-accent flex items-center justify-center">
          <SparkleIcon size={13} className="text-white" />
        </div>
        <span className="text-[14px] font-semibold text-ink tracking-tight">AI-Reader</span>
      </Link>
      <span className="text-xs text-ink-3">/</span>
      <Link href="/" className="text-[12.5px] text-ink-3 no-underline hover:text-ink-2 transition-colors">Library</Link>

      <div className="w-px h-5 bg-border" />

      <div className="flex-1 overflow-hidden min-w-0">
        <div className="text-[13px] text-ink font-medium truncate">{title}</div>
        <div className="text-[11px] text-ink-3 mt-px">{author}</div>
      </div>

      <div className="flex items-center gap-2 shrink-0">
        <span className="text-[11px] text-ink-3 whitespace-nowrap font-sans">
          {Math.round(progress)}% read
        </span>
        <div className="w-20 h-[3px] bg-sand-3 rounded-full overflow-hidden">
          <div
            className="h-full bg-accent rounded-full transition-[width] duration-100"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      <div className="w-px h-5 bg-border" />

      <button className="w-8 h-8 rounded-[var(--radius-sm)] border border-border bg-transparent cursor-pointer flex items-center justify-center">
        <SearchIcon size={15} className="text-ink-3" />
      </button>

      <button
        onClick={onToggleDrawer}
        className={`h-8 px-2.5 rounded-[var(--radius-sm)] border cursor-pointer flex items-center gap-1.5 text-xs font-medium font-sans transition-all ${
          drawerOpen
            ? 'border-border bg-accent-light text-accent'
            : 'border-border bg-transparent text-ink-2'
        }`}
      >
        <NotesIcon size={14} className={drawerOpen ? 'text-accent' : 'text-ink-3'} />
        Panel
      </button>
    </header>
  );
};