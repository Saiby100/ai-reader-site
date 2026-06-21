'use client';

import { Suspense, useCallback, useEffect, useRef, useState } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useReaderDocument } from '@/hooks/use-reader-document';
import { markDocumentViewedAction } from '@/actions/document-metadata-actions';
import { ReaderHeader } from '@/components/reader/reader-header';
import { ReaderContent } from '@/components/reader/reader-content';
import { DocumentRenderer } from '@/components/reader/document/document-renderer';
import { ReaderDrawer } from '@/components/reader/reader-drawer';

const ReaderPageContent = () => {
  const searchParams = useSearchParams();
  const id = searchParams.get('id');
  const { document, isLoading } = useReaderDocument(id);
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [progress, setProgress] = useState(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (document?.id) {
      markDocumentViewedAction(document.id);
    }
  }, [document?.id]);

  const handleScroll = useCallback(() => {
    const el = scrollRef.current;
    if (!el) return;
    const pct = (el.scrollTop / (el.scrollHeight - el.clientHeight)) * 100;
    setProgress(Math.min(100, Math.max(0, pct)));
  }, []);

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-sand">
        <p className="text-ink-3 text-sm">Loading document...</p>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="flex h-screen flex-col items-center justify-center gap-3 bg-sand">
        <p className="text-ink-3 text-sm">No document loaded.</p>
        <Link href="/" className="text-accent text-sm hover:underline">
          Back to Library
        </Link>
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-sand">
      <ReaderHeader
        title={document.title}
        author={document.author}
        progress={progress}
        drawerOpen={drawerOpen}
        onToggleDrawer={() => setDrawerOpen((o) => !o)}
      />
      <div className="flex flex-1 min-h-0 overflow-hidden">
        <ReaderContent ref={scrollRef} onScroll={handleScroll}>
          <DocumentRenderer tree={document.document} />
        </ReaderContent>
        <ReaderDrawer isOpen={drawerOpen} onToggle={() => setDrawerOpen((o) => !o)} documentId={document.id} />
      </div>
    </div>
  );
};

const ReaderPage = () => {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-sand">
          <p className="text-ink-3 text-sm">Loading document...</p>
        </div>
      }
    >
      <ReaderPageContent />
    </Suspense>
  );
};

export default ReaderPage;
