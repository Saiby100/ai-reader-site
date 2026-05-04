import { fetchDocumentMetadataList } from '@/lib/document-metadata-db';
import { MOCK_USER } from '@/lib/mock-user';
import { LibraryClient } from '@/components/library/library-client';

export const dynamic = 'force-dynamic';

const LibraryPage = async () => {
  const metadataList = await fetchDocumentMetadataList(MOCK_USER.id);

  return (
    <div className="mx-auto max-w-5xl px-6 py-8">
      <h1 className="text-2xl font-bold mb-6">My Library</h1>
      <LibraryClient metadataList={metadataList} />
    </div>
  );
};

export default LibraryPage;