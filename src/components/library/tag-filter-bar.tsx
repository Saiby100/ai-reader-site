type TagFilterBarProps = {
  /** Available tags to display as filter options */
  tags: string[];
  /** Currently selected tag, or null for "All" */
  activeTag: string | null;
  /** Callback when a tag is selected; null clears the filter */
  onTagSelect: (tag: string | null) => void;
};

const TagFilterBar = ({ tags, activeTag, onTagSelect }: TagFilterBarProps) => {
  return (
    <div className="flex gap-2 flex-wrap">
      <button
        onClick={() => onTagSelect(null)}
        className={`rounded-full px-3 py-1 text-sm border ${
          activeTag === null
            ? 'bg-gray-900 text-white border-gray-900 dark:bg-white dark:text-gray-900 dark:border-white'
            : 'border-gray-300 dark:border-gray-700'
        }`}
      >
        All
      </button>
      {tags.map((tag) => (
        <button
          key={tag}
          onClick={() => onTagSelect(tag)}
          className={`rounded-full px-3 py-1 text-sm border ${
            activeTag === tag
              ? 'bg-gray-900 text-white border-gray-900 dark:bg-white dark:text-gray-900 dark:border-white'
              : 'border-gray-300 dark:border-gray-700'
          }`}
        >
          {tag}
        </button>
      ))}
    </div>
  );
};

export { TagFilterBar };
