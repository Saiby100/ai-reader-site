'use client';

import { useMemo, useState } from 'react';
import { useRouter } from 'next/navigation';
import type { DocumentMetadata } from '@/types/document-metadata';
import { TagFilterBar } from '@/components/library/tag-filter-bar';
import { DocumentGrid } from '@/components/library/document-grid';
import { UploadForm } from '@/components/library/upload-form';

type LibraryClientProps = {
  /** Document metadata fetched server-side */
  metadataList: DocumentMetadata[];
};

export const LibraryClient = ({ metadataList }: LibraryClientProps) => {
  const router = useRouter();
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const allTags = useMemo(
    () => [...new Set(metadataList.flatMap((m) => m.tags))],
    [metadataList]
  );

  const filteredMetadata = activeTag
    ? metadataList.filter((m) => m.tags.includes(activeTag))
    : metadataList;

  const handleUploadComplete = () => {
    router.refresh();
  };

  return (
    <>
      <div className="mb-6">
        <UploadForm onUploadComplete={handleUploadComplete} />
      </div>

      {allTags.length > 0 && (
        <div className="mb-6">
          <TagFilterBar
            tags={allTags}
            activeTag={activeTag}
            onTagSelect={setActiveTag}
          />
        </div>
      )}

      <DocumentGrid metadataList={filteredMetadata} />
    </>
  );
};