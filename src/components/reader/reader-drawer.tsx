'use client';

import { useState } from 'react';
import { DrawerTabBar } from '@/components/reader/drawer-tab-bar';
import { NotesPanel } from '@/components/reader/notes-panel';

type ReaderDrawerProps = {
  /** Whether the drawer is currently open */
  isOpen: boolean;
  /** Document ID for loading notes */
  documentId: string;
};

export const ReaderDrawer = ({ isOpen, documentId }: ReaderDrawerProps) => {
  const [activeTab, setActiveTab] = useState('notes');

  return (
    <aside
      className={`shrink-0 border-l border-gray-200 bg-white transition-[width] duration-200
        dark:border-gray-800 dark:bg-gray-950 ${isOpen ? 'w-80' : 'w-0 overflow-hidden border-l-0'}`}
    >
      <div className="flex h-full w-80 flex-col">
        <DrawerTabBar activeTab={activeTab} onTabChange={setActiveTab} />
        {activeTab === 'notes' && <NotesPanel documentId={documentId} />}
      </div>
    </aside>
  );
};