'use client';

import { forwardRef, useCallback, type MouseEvent, type ReactNode } from 'react';

type ReaderContentProps = {
  /** Rendered document content (the parsed element tree as React nodes) */
  children: ReactNode;
  /** Scroll event handler for progress tracking */
  onScroll?: () => void;
};

export const ReaderContent = forwardRef<HTMLDivElement, ReaderContentProps>(
  ({ children, onScroll }, ref) => {
    // Internal page-jump links (rendered as `<a data-link-page>` by the renderer registry)
    // are handled here via event delegation, so the renderers stay server-safe. Scrolls to
    // the first element originating from the target page.
    const onClick = useCallback((event: MouseEvent<HTMLElement>) => {
      const anchor = (event.target as HTMLElement).closest('a[data-link-page]');
      if (!anchor) return;
      event.preventDefault();
      const page = anchor.getAttribute('data-link-page');
      const target = event.currentTarget.querySelector(`[data-page="${page}"]`);
      target?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, []);

    return (
      <main
        ref={ref}
        onScroll={onScroll}
        onClick={onClick}
        className="min-w-0 flex-1 overflow-x-hidden overflow-y-auto bg-sand"
      >
        <div
          className="mx-auto max-w-[860px] w-full px-8 py-12 font-serif text-[16.5px] leading-[1.8] text-ink wrap-anywhere
            [&_*]:max-w-full [&_pre]:whitespace-pre-wrap
            [&_h1]:font-serif [&_h1]:text-[30px] [&_h1]:font-semibold [&_h1]:leading-[1.25] [&_h1]:text-ink [&_h1]:mb-3.5
            [&_h2]:font-sans [&_h2]:text-[14px] [&_h2]:font-semibold [&_h2]:text-ink [&_h2]:mb-2 [&_h2]:tracking-[0.01em]
            [&_h3]:font-sans [&_h3]:text-[13px] [&_h3]:font-semibold [&_h3]:text-ink [&_h3]:mb-2
            [&_p]:mb-[22px] [&_p]:text-ink [&_p]:[text-wrap:pretty]
            [&_blockquote]:border-l-[3px] [&_blockquote]:border-amber [&_blockquote]:bg-amber-light [&_blockquote]:pl-3.5 [&_blockquote]:py-1.5 [&_blockquote]:rounded-r-[4px] [&_blockquote]:my-5
            [&_ul]:list-disc [&_ul]:pl-6 [&_ul]:mb-5
            [&_ol]:list-decimal [&_ol]:pl-6 [&_ol]:mb-5
            [&_li]:mb-1.5
            [&_a]:text-amber [&_a]:underline [&_a]:decoration-amber/40 [&_a]:underline-offset-2 [&_a]:cursor-pointer [&_a:hover]:decoration-amber"
        >
          {children}
        </div>
      </main>
    );
  }
);

ReaderContent.displayName = 'ReaderContent';
