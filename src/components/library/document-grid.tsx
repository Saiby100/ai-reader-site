import type { ReaderDocument } from '@/types/document';
import type { DocumentMetadata } from '@/types/document-metadata';
import { DocumentCard } from '@/components/library/document-card';

type DocumentGridProps = {
  /** List of documents to display */
  documents: ReaderDocument[];
  /** Metadata records keyed by document ID */
  metadataMap: Map<string, DocumentMetadata>;
};

const DocumentGrid = ({ documents, metadataMap }: DocumentGridProps) => {
  if (documents.length === 0) {
    return (
      <p className="text-gray-500 text-center py-12">
        No documents yet. Upload one to get started.
      </p>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {documents.map((doc) => (
        <DocumentCard key={doc.id} document={doc} metadata={metadataMap.get(doc.id) ?? null} />
      ))}
    </div>
  );
};

export { DocumentGrid };