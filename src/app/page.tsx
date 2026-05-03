'use client';

import { useState } from 'react';
import { useDocumentLibrary } from '@/hooks/use-reader-document';
import { TagFilterBar } from '@/components/library/tag-filter-bar';
import { DocumentGrid } from '@/components/library/document-grid';
import { UploadForm } from '@/components/library/upload-form';

const PLACEHOLDER_TAGS = ['Article', 'Research', 'Tutorial'];

const LibraryPage = () => {
  const { documents, isLoading, refresh } = useDocumentLibrary();
  const [activeTag, setActiveTag] = useState<string | null>(null);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">My Library</h1>

      <div className="mb-6">
        <UploadForm onUploadComplete={refresh} />
      </div>

      <div className="mb-6">
        <TagFilterBar
          tags={PLACEHOLDER_TAGS}
          activeTag={activeTag}
          onTagSelect={setActiveTag}
        />
      </div>

      {isLoading ? (
        <p className="text-gray-500 text-center py-12">Loading documents...</p>
      ) : (
        <DocumentGrid documents={documents} />
      )}
    </div>
  );
};

export default LibraryPage;
