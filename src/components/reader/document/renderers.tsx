import type { JSX, ReactNode } from 'react';
import type { DocumentElement } from '@/types/document-element';

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

export const renderers: RendererMap = {
  title: (el) => <h1 {...refAttrs(el)}>{el.text}</h1>,
  heading: (el) => {
    const level = Math.min(Math.max(el.level, 1), 6);
    const Tag = `h${level}` as keyof JSX.IntrinsicElements;
    return <Tag {...refAttrs(el)}>{el.text}</Tag>;
  },
  paragraph: (el) => <p {...refAttrs(el)}>{el.text}</p>,
  list_item: (el, children) => (
    <li {...refAttrs(el)}>
      {el.text}
      {children}
    </li>
  ),
  table: (el) => (
    <div {...refAttrs(el)} dangerouslySetInnerHTML={{ __html: el.html }} />
  ),
  image: (el) => <img {...refAttrs(el)} src={el.data_uri} alt="" />,
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
  caption: (el) => <figcaption {...refAttrs(el)}>{el.text}</figcaption>,
};
