'use client';

type ReaderDrawerProps = {
  /** Whether the drawer is currently open */
  isOpen: boolean;
};

export const ReaderDrawer = ({ isOpen }: ReaderDrawerProps) => {
  return (
    <aside
      className={`fixed right-0 top-0 h-full w-80 border-l border-gray-200 bg-white transition-transform duration-200 dark:border-gray-800 dark:bg-gray-950 ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      <div className="p-6">
        <h2 className="text-lg font-semibold">Panel</h2>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Notes, Q&amp;A, and comments will appear here.
        </p>
      </div>
    </aside>
  );
};
