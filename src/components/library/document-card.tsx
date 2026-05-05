'use client';

import Link from 'next/link';
import type { DocumentMetadata } from '@/types/document-metadata';
import type { DocColor } from '@/lib/doc-colors';
import { getColorSet } from '@/lib/doc-colors';
import { ProgressRing } from '@/components/library/progress-ring';
import { FileIcon, NotesIcon, ClockIcon, ChevronIcon } from '@/components/icons';

type ViewMode = 'grid' | 'list';

type DocumentCardProps = {
  /** Document metadata to display */
  metadata: DocumentMetadata;
  /** Color accent for this card */
  color: DocColor;
  /** Display mode */
  view: ViewMode;
  /** Reading progress percentage (0-100) */
  progress?: number;
  /** Number of notes on this document */
  noteCount?: number;
};

const formatRelativeDate = (date: Date): string => {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  if (diffDays < 14) return '1 week ago';
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
};

const DocumentCard = ({ metadata, color, view, progress = 0, noteCount = 0 }: DocumentCardProps) => {
  const { title, author, tags, created } = metadata;
  const c = getColorSet(color);

  if (view === 'list') {
    return (
      <Link
        href={`/reader?id=${metadata.id}`}
        className="flex items-center gap-4 py-3.5 px-[18px] rounded-[var(--radius)] border border-border bg-sand hover:bg-white cursor-pointer transition-all hover:shadow-[0_2px_12px_oklch(0%_0_0/0.07)]"
      >
        <div className="w-1 h-11 rounded-full shrink-0" style={{ background: c.spine }} />

        <div
          className="w-9 h-11 rounded-[var(--radius-sm)] flex items-center justify-center shrink-0"
          style={{ background: c.light }}
        >
          <span style={{ color: c.text }}><FileIcon size={18} /></span>
        </div>

        <div className="flex-1 min-w-0">
          <div className="text-[14px] font-medium text-ink font-serif mb-0.5 truncate">{title}</div>
          <div className="text-xs text-ink-3 flex items-center gap-2.5 flex-wrap">
            <span>{author || 'Unknown'}</span>
            <span className="text-sand-3">·</span>
            <span>{formatRelativeDate(created.timestamp)}</span>
          </div>
        </div>

        {tags.length > 0 && (
          <div className="flex gap-1 shrink-0">
            {tags.slice(0, 2).map((t) => (
              <span
                key={t}
                className="px-2 py-0.5 rounded-full text-[10.5px] font-medium"
                style={{ background: c.light, color: c.text }}
              >
                {t}
              </span>
            ))}
          </div>
        )}

        <div className="flex items-center gap-2 shrink-0">
          <ProgressRing pct={progress} size={30} color={c.spine} />
          <span className="text-[11px] text-ink-3 w-[30px]">{progress}%</span>
        </div>

        <div className="flex items-center gap-1 text-ink-3 shrink-0">
          <NotesIcon size={13} />
          <span className="text-[11px]">{noteCount}</span>
        </div>

        <ChevronIcon size={16} className="text-ink-3" />
      </Link>
    );
  }

  return (
    <Link
      href={`/reader?id=${metadata.id}`}
      className="rounded-[var(--radius-lg)] border border-border bg-white cursor-pointer overflow-hidden transition-all duration-[180ms] hover:-translate-y-[3px] hover:shadow-[0_8px_28px_oklch(0%_0_0/0.1)] shadow-[0_1px_4px_oklch(0%_0_0/0.04)] flex flex-col"
    >
      <div
        className="h-[100px] relative overflow-hidden"
        style={{ background: c.light, borderBottom: `3px solid ${c.spine}` }}
      >
        <div className="absolute inset-[18px_20px] flex flex-col gap-[7px]">
          {[1, 0.7, 0.85, 0.5, 0.65].map((w, i) => (
            <div
              key={i}
              className="h-[3px] rounded-full opacity-25"
              style={{ background: c.spine, width: `${w * 100}%` }}
            />
          ))}
        </div>
        <div className="absolute top-2.5 right-3">
          <ProgressRing pct={progress} size={32} color={c.spine} />
        </div>
      </div>

      <div className="p-[14px_16px] flex-1 flex flex-col gap-2">
        <div className="text-[13.5px] font-medium text-ink font-serif leading-[1.4]">{title}</div>
        <div className="text-[11.5px] text-ink-3 italic">
          {author || 'Unknown'} · {created.timestamp.getFullYear()}
        </div>

        {tags.length > 0 && (
          <div className="flex gap-1 flex-wrap">
            {tags.map((t) => (
              <span
                key={t}
                className="px-[7px] py-0.5 rounded-full text-[10px] font-medium"
                style={{ background: c.light, color: c.text }}
              >
                {t}
              </span>
            ))}
          </div>
        )}
      </div>

      <div className="px-4 py-2.5 border-t border-border flex items-center justify-between bg-sand">
        <span className="text-[11px] text-ink-3 flex items-center gap-1">
          <NotesIcon size={12} /> {noteCount} notes
        </span>
        <span className="text-[11px] text-ink-3 flex items-center gap-1">
          <ClockIcon size={11} /> {formatRelativeDate(created.timestamp)}
        </span>
      </div>
    </Link>
  );
};

export { DocumentCard };