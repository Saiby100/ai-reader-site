import Link from 'next/link';
import type { ReaderDocument } from '@/types/document';

type DocumentCardProps = {
  /** The document to display */
  document: ReaderDocument;
};

const PLACEHOLDER_TAGS = ['Article'];
const PLACEHOLDER_UPLOADED = 'Jan 1, 2025';
const PLACEHOLDER_LAST_VIEWED = 'Never';

const DocumentCard = ({ document }: DocumentCardProps) => {
  const author = document.author || 'Unknown Author';

  return (
    <Link
      href={`/reader?id=${document.id}`}
      className="block rounded border border-gray-200 p-4 hover:border-gray-400 dark:border-gray-700 dark:hover:border-gray-500"
    >
      <div className="flex gap-1 mb-2">
        {PLACEHOLDER_TAGS.map((tag) => (
          <span
            key={tag}
            className="rounded-full bg-gray-100 px-2 py-0.5 text-xs dark:bg-gray-800"
          >
            {tag}
          </span>
        ))}
      </div>

      <h3 className="font-medium">{document.title}</h3>
      <p className="text-sm text-gray-500">{author}</p>

      <div className="mt-3 flex justify-between text-xs text-gray-400">
        <span>Uploaded: {PLACEHOLDER_UPLOADED}</span>
        <span>Viewed: {PLACEHOLDER_LAST_VIEWED}</span>
      </div>
    </Link>
  );
};

export { DocumentCard };
