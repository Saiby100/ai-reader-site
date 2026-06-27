'use client';

import { useCallback, useState } from 'react';

/**
 * Owns the state for the reader's image-enlarge popup. Images render at a modest,
 * secondary inline size; opening the lightbox shows the full-resolution source.
 * `src` is the currently-zoomed image data URI, or `null` when the popup is closed.
 */
export const useImageLightbox = () => {
  const [src, setSrc] = useState<string | null>(null);

  const open = useCallback((next: string) => setSrc(next), []);
  const close = useCallback(() => setSrc(null), []);

  return { src, open, close };
};
