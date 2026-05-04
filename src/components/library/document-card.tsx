import Link from 'next/link';
import type { ReaderDocument } from '@/types/document';
import type { DocumentMetadata } from '@/types/document-metadata';

type DocumentCardProps = {
  /** The document to display */
  document: ReaderDocument;
  /** Metadata from the document store (null if not yet loaded) */
  metadata: DocumentMetadata | null;
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const DocumentCard = ({ document, metadata }: DocumentCardProps) => {
  const author = metadata?.author || document.author || 'Unknown Author';
  const tags = metadata?.tags ?? [];
  const created = metadata?.createdStamp.timestamp;
  const viewed = metadata?.viewedStamp?.timestamp;

  return (
    <Link
      href={`/reader?id=${document.id}`}
      className="block rounded border border-gray-200 p-4 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-500"
    >
      {tags.length > 0 && (
        <div className="flex gap-1 mb-2 overflow-x-auto scrollbar-hide">
          {tags.map((tag) => (
            <span
              key={tag}
              className="shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-800"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <h3 className="font-medium">{document.title}</h3>
      <p className="text-sm text-gray-500">{author}</p>

      <div className="mt-3 flex justify-between text-xs text-gray-400">
        <span>Uploaded: {created ? formatDate(created) : '—'}</span>
        <span>Viewed: {viewed ? formatDate(viewed) : 'Never'}</span>
      </div>
    </Link>
  );
};

export { DocumentCard };