'use client';

import { SearchIcon, GridIcon, ListIcon, SparkleIcon } from '@/components/icons';

type ViewMode = 'grid' | 'list';

type TopBarProps = {
  /** Current search query */
  query: string;
  /** Callback when search query changes */
  onQueryChange: (query: string) => void;
  /** Current view mode */
  view: ViewMode;
  /** Callback when view mode changes */
  onViewChange: (view: ViewMode) => void;
};

export const TopBar = ({ query, onQueryChange, view, onViewChange }: TopBarProps) => {
  return (
    <div className="sticky top-0 z-50 border-b border-border bg-sand/92 backdrop-blur-[12px] px-8 h-14 flex items-center gap-4">
      <div className="flex items-center gap-2">
        <div className="w-7 h-7 rounded-[var(--radius-sm)] bg-accent flex items-center justify-center">
          <SparkleIcon size={14} className="text-white" />
        </div>
        <span className="text-[15px] font-semibold tracking-tight text-ink">AI-Reader</span>
      </div>

      <div className="w-px h-5 bg-border" />

      <div className="flex-1 max-w-[400px] relative">
        <div className="absolute left-2.5 top-1/2 -translate-y-1/2">
          <SearchIcon size={14} className="text-ink-3" />
        </div>
        <input
          value={query}
          onChange={(e) => onQueryChange(e.target.value)}
          placeholder="Search by title, author, or tag…"
          className="w-full py-[7px] pl-8 pr-3 rounded-[var(--radius)] border border-border text-[13px] font-sans bg-white text-ink outline-none placeholder:text-ink-3"
        />
      </div>

      <div className="ml-auto flex items-center gap-1.5">
        <div className="flex border border-border rounded-[var(--radius-sm)] overflow-hidden">
          <button
            onClick={() => onViewChange('grid')}
            className={`w-8 h-[30px] flex items-center justify-center border-r border-border cursor-pointer transition-colors ${
              view === 'grid' ? 'bg-sand-2' : 'bg-white'
            }`}
          >
            <GridIcon size={14} className={view === 'grid' ? 'text-ink' : 'text-ink-3'} />
          </button>
          <button
            onClick={() => onViewChange('list')}
            className={`w-8 h-[30px] flex items-center justify-center cursor-pointer transition-colors ${
              view === 'list' ? 'bg-sand-2' : 'bg-white'
            }`}
          >
            <ListIcon size={14} className={view === 'list' ? 'text-ink' : 'text-ink-3'} />
          </button>
        </div>
      </div>
    </div>
  );
};
