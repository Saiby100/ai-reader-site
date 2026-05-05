import { fetchDocumentMetadataList } from '@/lib/document-metadata-db';
import { MOCK_USER } from '@/lib/mock-user';
import { LibraryClient } from '@/components/library/library-client';

export const dynamic = 'force-dynamic';

const LibraryPage = async () => {
  const metadataList = await fetchDocumentMetadataList(MOCK_USER.id);

  return (
    <div className="min-h-screen bg-sand">
      <LibraryClient metadataList={metadataList} />
    </div>
  );
};

export default LibraryPage;