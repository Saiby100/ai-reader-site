'use client';

import { useState } from 'react';
import { DrawerTabBar } from '@/components/reader/drawer-tab-bar';
import { NotesPanel } from '@/components/reader/notes-panel';
import { ChevronIcon } from '@/components/icons';

type ReaderDrawerProps = {
  /** Whether the drawer is currently open */
  isOpen: boolean;
  /** Callback to toggle open/close */
  onToggle: () => void;
  /** Document ID for loading notes */
  documentId: string;
};

export const ReaderDrawer = ({ isOpen, onToggle, documentId }: ReaderDrawerProps) => {
  const [activeTab, setActiveTab] = useState('notes');

  return (
    <aside
      className="shrink-0 relative flex flex-col bg-white transition-[width,min-width] duration-[280ms] ease-[cubic-bezier(0.4,0,0.2,1)] overflow-hidden"
      style={{
        width: isOpen ? 340 : 0,
        minWidth: isOpen ? 340 : 0,
        borderLeft: isOpen ? '1px solid var(--border)' : 'none',
      }}
    >
      {/* Edge toggle handle */}
      <button
        onClick={onToggle}
        className="absolute -left-[17px] top-1/2 -translate-y-1/2 w-[18px] h-14 bg-white border border-border border-r-0 rounded-l-[6px] cursor-pointer flex items-center justify-center z-10 shadow-[-2px_0_6px_oklch(0%_0_0/0.04)] hover:bg-sand transition-colors"
        title={isOpen ? 'Collapse panel' : 'Expand panel'}
      >
        <ChevronIcon size={14} className={`text-ink-3 transition-transform ${isOpen ? '' : 'rotate-180'}`} />
      </button>

      {isOpen && (
        <div className="w-[340px] h-full flex flex-col">
          <DrawerTabBar activeTab={activeTab} onTabChange={setActiveTab} />
          {activeTab === 'notes' && <NotesPanel documentId={documentId} />}
          {activeTab === 'qa' && (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-xs text-ink-3 text-center">Q&A practice coming soon.</p>
            </div>
          )}
          {activeTab === 'comments' && (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-xs text-ink-3 text-center">Discussion coming soon.</p>
            </div>
          )}
          {activeTab === 'ai' && (
            <div className="flex-1 flex items-center justify-center p-4">
              <p className="text-xs text-ink-3 text-center">Ask AI coming soon.</p>
            </div>
          )}
        </div>
      )}
    </aside>
  );
};
