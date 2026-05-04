import type { DocumentMetadata } from '@/types/document-metadata';
import { DocumentCard } from '@/components/library/document-card';

type DocumentGridProps = {
  /** List of document metadata to display */
  metadataList: DocumentMetadata[];
};

const DocumentGrid = ({ metadataList }: DocumentGridProps) => {
  if (metadataList.length === 0) {
    return (
      <p className="text-gray-500 text-center py-12">
        No documents yet. Upload one to get started.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {metadataList.map((metadata) => (
        <DocumentCard key={metadata.id} metadata={metadata} />
      ))}
    </div>
  );
};

export { DocumentGrid };
