/**
 * Shared contract for parsed documents, mirroring the parser service response
 * (`services/parser/app/models.py`). The wire format is snake_case to match the
 * Python response directly, so no field transform is needed on either side.
 *
 * This is the single source of truth the client renders from. The parser service
 * owns the one-and-only translation from docling's model into this shape.
 */

/** Discriminator for the kind of a parsed element. */
export type ElementType =
  | 'title'
  | 'heading'
  | 'paragraph'
  | 'list_item'
  | 'table'
  | 'image'
  | 'code'
  | 'formula'
  | 'caption';

/** Source-location + identity metadata carried by every parsed element. */
type ElementMeta = {
  /** Docling self_ref JSON-pointer (e.g. '#/texts/12') — stable anchor for citations, click-to-source, and highlighting. */
  ref?: string | null;
  /** 1-based source page the element originated from, when known. */
  page?: number | null;
  /** Raw docling DocItemLabel, preserved so distinctions the renderer collapses (caption vs footnote) stay queryable. */
  label?: string | null;
  /** Character span [start, end] within the element's source text, for precise sub-element highlighting. */
  charspan?: [number, number] | null;
  /** Horizontal text alignment inferred from source geometry; absent/null means default (left). PDF-only. */
  alignment?: 'center' | 'right' | null;
  /** External URL this element hyperlinks to (PDF /URI link, or a docx/html/md hyperlink), when any. */
  link_href?: string | null;
  /** 1-based page this element links to via an internal PDF /GoTo link, for in-document navigation. */
  link_target_page?: number | null;
};

/** Top-level document title. */
export type TitleElement = ElementMeta & {
  /** Element kind. */
  type: 'title';
  /** Title text. */
  text: string;
};

/** Section heading with a depth level. */
export type HeadingElement = ElementMeta & {
  /** Element kind. */
  type: 'heading';
  /** Heading depth (1-6). */
  level: number;
  /** Heading text. */
  text: string;
};

/** Body paragraph. */
export type ParagraphElement = ElementMeta & {
  /** Element kind. */
  type: 'paragraph';
  /** Paragraph text. */
  text: string;
};

/** A single list item, optionally containing nested elements. */
export type ListItemElement = ElementMeta & {
  /** Element kind. */
  type: 'list_item';
  /** Item text. */
  text: string;
  /** Nested child elements, e.g. a sub-list. */
  children?: DocumentElement[];
};

/** Table, carrying docling's pre-rendered HTML. */
export type TableElement = ElementMeta & {
  /** Element kind. */
  type: 'table';
  /** Pre-rendered table HTML. */
  html: string;
};

/** Raster image as an inline data URI. */
export type ImageElement = ElementMeta & {
  /** Element kind. */
  type: 'image';
  /** Inline data URI for the image. */
  data_uri: string;
};

/** Code block with optional detected language. */
export type CodeElement = ElementMeta & {
  /** Element kind. */
  type: 'code';
  /** Code text. */
  text: string;
  /** Detected source language, when known. */
  language?: string | null;
};

/** Mathematical formula, carrying its LaTeX source. */
export type FormulaElement = ElementMeta & {
  /** Element kind. */
  type: 'formula';
  /** LaTeX source of the formula. */
  text: string;
};

/** Figure/table caption. */
export type CaptionElement = ElementMeta & {
  /** Element kind. */
  type: 'caption';
  /** Caption text. */
  text: string;
};

/** A single node in the parsed document tree. */
export type DocumentElement =
  | TitleElement
  | HeadingElement
  | ParagraphElement
  | ListItemElement
  | TableElement
  | ImageElement
  | CodeElement
  | FormulaElement
  | CaptionElement;

/** Docling's quality assessment of the parse. */
export type ParseConfidence = {
  /** Overall grade: poor / fair / good / excellent / unspecified. */
  grade: string;
  /** Mean confidence score in [0, 1], when available. */
  score?: number | null;
};

/** Document-level metadata about a parse operation. */
export type ParseMetadata = {
  /** Original uploaded filename. */
  filename: string;
  /** Number of pages in the source document. */
  page_count: number;
  /** File format inferred from the extension. */
  format_detected: string;
  /** Wall-clock parse time in milliseconds. */
  parse_duration_ms: number;
  /** Docling ConversionStatus: success / partial_success / failure / skipped. */
  status: string;
  /** Docling confidence report, when available. */
  confidence?: ParseConfidence | null;
  /** Content hash of the source file — usable as a cache / dedup key. */
  binary_hash?: string | null;
};

/** Top-level response from the parser service `/parse` endpoint. */
export type ParseResponse = {
  /** Ordered, render-ready document tree. */
  document: DocumentElement[];
  /** Document-level metadata. */
  metadata: ParseMetadata;
  /** Human-readable parse errors, when any. */
  errors: string[];
};
