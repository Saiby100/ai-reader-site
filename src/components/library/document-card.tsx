import Link from 'next/link';
import type { DocumentMetadata } from '@/types/document-metadata';

type DocumentCardProps = {
  /** Document metadata to display */
  metadata: DocumentMetadata;
};

const formatDate = (date: Date): string => {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
};

const DocumentCard = ({ metadata }: DocumentCardProps) => {
  const { title, author, tags, created, viewed } = metadata;

  return (
    <Link
      href={`/reader?id=${metadata.id}`}
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

      <h3 className="font-medium">{title}</h3>
      <p className="text-sm text-gray-500">{author || 'Unknown Author'}</p>

      <div className="mt-3 flex justify-between text-xs text-gray-400">
        <span>Uploaded: {formatDate(created.timestamp)}</span>
        <span>Viewed: {viewed ? formatDate(viewed.timestamp) : 'Never'}</span>
      </div>
    </Link>
  );
};

export { DocumentCard };
