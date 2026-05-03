type ReaderHeaderProps = {
  /** Document title */
  title: string;
  /** Document author */
  author: string;
};

export const ReaderHeader = ({ title, author }: ReaderHeaderProps) => {
  return (
    <header className="px-6 py-4">
      <h1 className="text-2xl font-bold">{title}</h1>
      <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">{author}</p>
    </header>
  );
};
