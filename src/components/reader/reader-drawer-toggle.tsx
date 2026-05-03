type ReaderDrawerToggleProps = {
  /** Whether the drawer is currently open */
  isOpen: boolean;
  /** Callback to toggle the drawer */
  onToggle: () => void;
};

export const ReaderDrawerToggle = ({ isOpen, onToggle }: ReaderDrawerToggleProps) => {
  return (
    <button
      onClick={onToggle}
      className="rounded border border-gray-300 px-3 py-1 text-sm hover:bg-gray-100 dark:border-gray-700 dark:hover:bg-gray-800"
    >
      {isOpen ? 'Close Panel' : 'Open Panel'}
    </button>
  );
};
