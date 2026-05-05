'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { DocumentMetadata } from '@/types/document-metadata';
import { TopBar } from '@/components/library/top-bar';
import { TagFilterBar } from '@/components/library/tag-filter-bar';
import { DocumentGrid } from '@/components/library/document-grid';
import { UploadForm } from '@/components/library/upload-form';

type ViewMode = 'grid' | 'list';

type LibraryClientProps = {
  /** Document metadata fetched server-side */
  metadataList: DocumentMetadata[];
};

export const LibraryClient = ({ metadataList }: LibraryClientProps) => {
  const router = useRouter();
  const [activeTag, setActiveTag] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [view, setView] = useState<ViewMode>('grid');

  const allTags = useMemo(
    () => [...new Set(metadataList.flatMap((m) => m.tags))],
    [metadataList]
  );

  const filteredMetadata = useMemo(() => {
    const q = query.toLowerCase();
    return metadataList.filter((m) => {
      const matchQuery = !q
        || m.title.toLowerCase().includes(q)
        || m.author.toLowerCase().includes(q)
        || m.tags.some((t) => t.toLowerCase().includes(q));
      const matchTag = !activeTag || m.tags.includes(activeTag);
      return matchQuery && matchTag;
    });
  }, [metadataList, query, activeTag]);

  const inProgressCount = metadataList.filter(() => false).length; // placeholder - no progress tracking yet

  const handleUploadComplete = () => {
    router.refresh();
  };

  return (
    <>
      <TopBar query={query} onQueryChange={setQuery} view={view} onViewChange={setView} />

      <div className="max-w-[1100px] mx-auto px-8 pt-9 pb-[60px]">
        <div className="flex items-end justify-between mb-7">
          <div>
            <h1 className="font-serif text-[26px] font-semibold text-ink mb-1">Your Library</h1>
            <p className="text-[13.5px] text-ink-3">
              {metadataList.length} documents{inProgressCount > 0 ? ` · ${inProgressCount} in progress` : ''}
            </p>
          </div>
          <UploadForm onUploadComplete={handleUploadComplete} />
        </div>

        {allTags.length > 0 && (
          <div className="mb-7">
            <TagFilterBar
              tags={allTags}
              activeTag={activeTag}
              onTagSelect={setActiveTag}
            />
          </div>
        )}

        <DocumentGrid metadataList={filteredMetadata} view={view} />
      </div>
    </>
  );
};