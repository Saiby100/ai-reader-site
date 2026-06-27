'use client';

import { forwardRef, useCallback, type MouseEvent, type ReactNode } from 'react';

import { useImageLightbox } from '@/hooks/use-image-lightbox';
import { ImageLightbox } from './image-lightbox';

type ReaderContentProps = {
  /** Rendered document content (the parsed element tree as React nodes) */
  children: ReactNode;
  /** Scroll event handler for progress tracking */
  onScroll?: () => void;
};

export const ReaderContent = forwardRef<HTMLDivElement, ReaderContentProps>(
  ({ children, onScroll }, ref) => {
    const { src: zoomedSrc, open: openZoom, close: closeZoom } = useImageLightbox();

    // Clicks on rendered content are handled here via event delegation, so the renderers stay
    // server-safe. Two cases: zoomable images (rendered as `<img data-zoomable>`) open the
    // lightbox; internal page-jump links (`<a data-link-page>`) scroll to the first element
    // originating from the target page.
    const onClick = useCallback(
      (event: MouseEvent<HTMLElement>) => {
        const target = event.target as HTMLElement;

        const image = target.closest('img[data-zoomable]');
        if (image) {
          const src = image.getAttribute('src');
          if (src) openZoom(src);
          return;
        }

        const anchor = target.closest('a[data-link-page]');
        if (!anchor) return;
        event.preventDefault();
        const page = anchor.getAttribute('data-link-page');
        const pageTarget = event.currentTarget.querySelector(`[data-page="${page}"]`);
        pageTarget?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      },
      [openZoom]
    );

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
            [&_img]:block [&_img]:mx-auto [&_img]:my-6 [&_img]:h-auto [&_img]:w-auto [&_img]:max-h-[420px] [&_img]:rounded-[4px] [&_img]:object-contain [&_img]:cursor-zoom-in
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
        <ImageLightbox src={zoomedSrc} onClose={closeZoom} />
      </main>
    );
  }
);

ReaderContent.displayName = 'ReaderContent';
