'use client';

import { Suspense, useEffect, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useReaderDocument } from '@/hooks/use-reader-document';
import { useMarkDocumentViewed } from '@/hooks/use-document-metadata';
import { ReaderHeader } from '@/components/reader/reader-header';
import { ReaderContent } from '@/components/reader/reader-content';
import { ReaderDrawer } from '@/components/reader/reader-drawer';
import { ReaderDrawerToggle } from '@/components/reader/reader-drawer-toggle';

const ReaderPageContent = () => {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');
  const { document, isLoading } = useReaderDocument(id);
  const { markViewed } = useMarkDocumentViewed();
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    if (document?.id) {
      markViewed(document.id);
    }
  }, [document?.id, markViewed]);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-gray-500">Loading document...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-2">
        <p className="text-gray-500">No document loaded.</p>
        <Link href="/" className="text-blue-600 underline hover:text-blue-800">
          Go back
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col">
      <div className="flex items-center justify-between border-b border-gray-200 dark:border-gray-800">
        <ReaderHeader title={document.title} author={document.author} />
        <div className="pr-4">
          <ReaderDrawerToggle isOpen={drawerOpen} onToggle={() => setDrawerOpen(!drawerOpen)} />
        </div>
      </div>
      <ReaderContent htmlContent={document.htmlContent} />
      <ReaderDrawer isOpen={drawerOpen} />
    </div>
  );
};

const ReaderPage = () => {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center">
          <p className="text-gray-500">Loading document...</p>
        </div>
      }
    >
      <ReaderPageContent />
    </Suspense>
  );
};

export default ReaderPage;
