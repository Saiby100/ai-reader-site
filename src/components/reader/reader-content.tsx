'use client';

type ReaderContentProps = {
  /** Normalized HTML string to render as document content */
  htmlContent: string;
};

export const ReaderContent = ({ htmlContent }: ReaderContentProps) => {
  return (
    <main className="flex-1 overflow-y-auto px-6 py-4">
      <div
        className="mx-auto max-w-3xl"
        dangerouslySetInnerHTML={{ __html: htmlContent }}
      />
    </main>
  );
};
