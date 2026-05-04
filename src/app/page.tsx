'use client';

import { useMemo, useState } from 'react';
import { useDocumentLibrary } from '@/hooks/use-reader-document';
import { useDocumentMetadataLibrary } from '@/hooks/use-document-metadata';
import { TagFilterBar } from '@/components/library/tag-filter-bar';
import { DocumentGrid } from '@/components/library/document-grid';
import { UploadForm } from '@/components/library/upload-form';

const LibraryPage = () => {
  const { documents, isLoading: docsLoading, refresh: refreshDocs } = useDocumentLibrary();
  const { metadataList, isLoading: metaLoading, refresh: refreshMeta } = useDocumentMetadataLibrary();
  const [activeTag, setActiveTag] = useState<string | null>(null);

  const metadataMap = useMemo(
    () => new Map(metadataList.map((m) => [m.id, m])),
    [metadataList]
  );

  const allTags = useMemo(
    () => [...new Set(metadataList.flatMap((m) => m.tags))],
    [metadataList]
  );

  const filteredDocuments = activeTag
    ? documents.filter((doc) => metadataMap.get(doc.id)?.tags.includes(activeTag))
    : documents;

  const handleUploadComplete = () => {
    refreshDocs();
    refreshMeta();
  };

  const isLoading = docsLoading || metaLoading;

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">My Library</h1>

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

      {isLoading ? (
        <p className="text-gray-500 text-center py-12">Loading documents...</p>
      ) : (
        <DocumentGrid documents={filteredDocuments} metadataMap={metadataMap} />
      )}
    </div>
  );
};

export default LibraryPage;