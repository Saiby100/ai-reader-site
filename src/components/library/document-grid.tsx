import type { DocumentMetadata } from '@/types/document-metadata';
import { DocumentCard } from '@/components/library/document-card';
import { getColorForIndex } from '@/lib/doc-colors';

type ViewMode = 'grid' | 'list';

type DocumentGridProps = {
  /** List of document metadata to display */
  metadataList: DocumentMetadata[];
  /** Display mode */
  view: ViewMode;
};

const DocumentGrid = ({ metadataList, view }: DocumentGridProps) => {
  if (metadataList.length === 0) {
    return (
      <div className="text-center py-[60px] text-ink-3">
        <p className="text-sm">No documents match your search.</p>
      </div>
    );
  }

  const containerClass = view === 'grid'
    ? 'grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4'
    : 'flex flex-col gap-2';

  return (
    <div className={containerClass}>
      {metadataList.map((metadata, i) => (
        <DocumentCard
          key={metadata.id}
          metadata={metadata}
          color={getColorForIndex(i)}
          view={view}
        />
      ))}
    </div>
  );
};

export { DocumentGrid };