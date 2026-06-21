import { Fragment, type ReactNode } from 'react';
import type { DocumentElement } from '@/types/document-element';
import { renderers } from './renderers';

type DocumentRendererProps = {
  /** Ordered, render-ready document tree from the parser service. */
  tree: DocumentElement[];
};

const hasChildren = (
  el: DocumentElement
): el is Extract<DocumentElement, { children?: DocumentElement[] }> =>
  'children' in el && Array.isArray(el.children) && el.children.length > 0;

const renderElement = (el: DocumentElement, index: number): ReactNode => {
  const children = hasChildren(el) ? el.children!.map(renderElement) : null;
  // The registry is keyed by `type`; the cast collapses the per-type renderer
  // signatures into the common element shape after the lookup.
  const render = renderers[el.type] as (
    el: DocumentElement,
    children: ReactNode
  ) => ReactNode;

  return <Fragment key={el.ref ?? index}>{render(el, children)}</Fragment>;
};

/**
 * Renders a parsed document tree into React nodes via the renderer registry.
 * Each element becomes a real DOM node carrying its `data-ref`, so downstream
 * features (citations, click-to-source, highlighting) can address elements.
 */
export const DocumentRenderer = ({ tree }: DocumentRendererProps) => (
  <>{tree.map(renderElement)}</>
);
