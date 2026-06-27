import type { CSSProperties, JSX, ReactNode } from 'react';
import type { DocumentElement, ImageElement } from '@/types/document-element';

/**
 * Renders one element. `children` is the already-rendered subtree (for elements
 * that nest, e.g. list items); most renderers ignore it.
 */
type ElementRenderer<T extends DocumentElement> = (el: T, children: ReactNode) => ReactNode;

/**
 * Registry mapping each element `type` to its renderer. The mapped type forces a
 * renderer to exist for every member of the `DocumentElement` union — adding a new
 * element type without a renderer is a compile error.
 */
type RendererMap = { [T in DocumentElement as T['type']]: ElementRenderer<T> };

/** Reference metadata attached to the rendered DOM node, for later interactivity. */
const refAttrs = (el: DocumentElement) => ({
  'data-ref': el.ref ?? undefined,
  'data-page': el.page ?? undefined,
  style: el.alignment ? { textAlign: el.alignment } : undefined,
});

/**
 * Alignment style for an image. An `<img>` is inline, so `text-align` on the img
 * itself does nothing (it aligns the img's content, not the img) — center/right it
 * with auto margins on a block-displayed image instead.
 */
const imageStyle = (el: ImageElement): CSSProperties | undefined => {
  if (el.alignment === 'center') return { display: 'block', margin: '0 auto' };
  if (el.alignment === 'right') return { display: 'block', marginLeft: 'auto' };
  return undefined;
};

/**
 * Wraps an element's text in an anchor when it carries a link. External links
 * (`link_href`) open in a new tab; internal page-jumps (`link_target_page`) render an
 * anchor tagged with `data-link-page` — `ReaderContent` intercepts the click and scrolls
 * to that page, so no per-element handler is needed here (keeps renderers server-safe).
 */
const linkWrap = (el: DocumentElement, content: ReactNode): ReactNode => {
  if (el.link_href) {
    return (
      <a href={el.link_href} target="_blank" rel="noopener noreferrer">
        {content}
      </a>
    );
  }
  if (el.link_target_page != null) {
    return (
      <a href="#" data-link-page={el.link_target_page}>
        {content}
      </a>
    );
  }
  return content;
};

export const renderers: RendererMap = {
  title: (el) => <h1 {...refAttrs(el)}>{linkWrap(el, el.text)}</h1>,
  heading: (el) => {
    const level = Math.min(Math.max(el.level, 1), 6);
    const Tag = `h${level}` as keyof JSX.IntrinsicElements;
    return <Tag {...refAttrs(el)}>{linkWrap(el, el.text)}</Tag>;
  },
  paragraph: (el) => <p {...refAttrs(el)}>{linkWrap(el, el.text)}</p>,
  list_item: (el, children) => (
    <li {...refAttrs(el)}>
      {linkWrap(el, el.text)}
      {children}
    </li>
  ),
  table: (el) => (
    <div {...refAttrs(el)} dangerouslySetInnerHTML={{ __html: el.html }} />
  ),
  image: (el) => (
    <img {...refAttrs(el)} style={imageStyle(el)} src={el.data_uri} alt="" />
  ),
  code: (el) => (
    <pre {...refAttrs(el)}>
      <code data-language={el.language ?? undefined}>{el.text}</code>
    </pre>
  ),
  // Rendered as raw LaTeX for now; a later feature can swap in KaTeX off `data-ref`.
  formula: (el) => (
    <span {...refAttrs(el)} data-formula>
      {el.text}
    </span>
  ),
  caption: (el) => <figcaption {...refAttrs(el)}>{linkWrap(el, el.text)}</figcaption>,
};
