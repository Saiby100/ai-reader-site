'use client';

import { useEffect } from 'react';

type ImageLightboxProps = {
  /** Data URI of the image to show full-size, or `null` when the popup is closed. */
  src: string | null;
  /** Called to dismiss the popup (backdrop click, close button, or Escape). */
  onClose: () => void;
};

/**
 * Full-viewport popup that shows a reader image at full resolution. Inline images are
 * intentionally small (secondary to the text); this gives the reader a way to inspect
 * detail on demand. Closes on backdrop click, the ✕ button, or Escape, and locks body
 * scroll while open.
 */
export const ImageLightbox = ({ src, onClose }: ImageLightboxProps) => {
  useEffect(() => {
    if (!src) return;

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKeyDown);

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [src, onClose]);

  if (!src) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      onClick={onClose}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6 cursor-zoom-out"
    >
      <button
        type="button"
        onClick={onClose}
        aria-label="Close"
        className="absolute right-4 top-4 flex h-10 w-10 items-center justify-center rounded-full bg-white/10 text-2xl leading-none text-white hover:bg-white/20"
      >
        ✕
      </button>
      {/* Stop propagation so clicking the image itself doesn't dismiss the popup. */}
      <img
        src={src}
        alt=""
        onClick={(event) => event.stopPropagation()}
        className="max-h-[90vh] max-w-[90vw] object-contain cursor-default"
      />
    </div>
  );
};
