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
    <div className="flex gap-1.5 flex-wrap">
      <button
        onClick={() => onTagSelect(null)}
        className={`px-3 py-[5px] rounded-full border text-xs cursor-pointer transition-all font-sans ${
          activeTag === null
            ? 'border-accent bg-accent-light text-accent font-semibold'
            : 'border-border bg-white text-ink-3 font-normal'
        }`}
      >
        All
      </button>
      {tags.map((tag) => (
        <button
          key={tag}
          onClick={() => onTagSelect(tag)}
          className={`px-3 py-[5px] rounded-full border text-xs cursor-pointer transition-all font-sans ${
            activeTag === tag
              ? 'border-accent bg-accent-light text-accent font-semibold'
              : 'border-border bg-white text-ink-3 font-normal'
          }`}
        >
          {tag}
        </button>
      ))}
    </div>
  );
};

export { TagFilterBar };