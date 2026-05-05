'use client';

import { NotesIcon, SparkleIcon } from '@/components/icons';

type DrawerTabBarProps = {
  /** Currently active tab id */
  activeTab: string;
  /** Callback when a tab is selected */
  onTabChange: (tab: string) => void;
};

const QAIcon = ({ size = 16, className }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="10" cy="10" r="7" />
    <path d="M10 14v.5M10 7c0-1.1.9-2 2-2s2 .9 2 2c0 1.5-2 2-2 3" />
  </svg>
);

const CommentsIcon = ({ size = 16, className }: { size?: number; className?: string }) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M3 4h14v10H9l-4 3V14H3V4z" />
  </svg>
);

const TABS = [
  { id: 'notes', label: 'Notes', Icon: NotesIcon },
  { id: 'qa', label: 'Q&A', Icon: QAIcon },
  { id: 'comments', label: 'Discussion', Icon: CommentsIcon },
  { id: 'ai', label: 'Ask AI', Icon: SparkleIcon },
];

export const DrawerTabBar = ({ activeTab, onTabChange }: DrawerTabBarProps) => {
  return (
    <div className="px-4 pt-4 border-b border-border">
      <div className="text-[12px] font-semibold text-ink-3 mb-3 tracking-[0.06em] uppercase">Research Panel</div>
      <div className="flex gap-0">
        {TABS.map((tab) => {
          const isAI = tab.id === 'ai';
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => onTabChange(tab.id)}
              className={`flex-1 py-[7px] px-0.5 border-none cursor-pointer flex items-center justify-center gap-1 text-[11.5px] font-sans transition-all rounded-t-[var(--radius-sm)] ${
                isAI && active
                  ? 'bg-accent text-white font-semibold'
                  : isAI
                  ? 'bg-accent-light text-accent font-normal'
                  : active
                  ? 'bg-transparent text-accent font-semibold border-b-2 border-b-accent'
                  : 'bg-transparent text-ink-3 font-normal border-b-2 border-b-transparent'
              }`}
            >
              <tab.Icon size={12} className={
                isAI && active ? 'text-white'
                : isAI ? 'text-accent'
                : active ? 'text-accent'
                : 'text-ink-3'
              } />
              {tab.label}
            </button>
          );
        })}
      </div>
    </div>
  );
};