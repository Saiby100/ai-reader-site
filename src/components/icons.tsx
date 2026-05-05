type IconProps = {
  /** Icon size in pixels */
  size?: number;
  /** Additional CSS classes */
  className?: string;
};

export const SparkleIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="currentColor" className={className}>
    <path d="M10 2l1.5 5.5L17 9l-5.5 1.5L10 16l-1.5-5.5L3 9l5.5-1.5L10 2z" />
  </svg>
);

export const UploadIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M10 13V5M6 9l4-4 4 4" />
    <path d="M4 15h12" />
  </svg>
);

export const SearchIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="9" cy="9" r="5" />
    <path d="M16 16l-3.5-3.5" />
  </svg>
);

export const GridIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <rect x="3" y="3" width="6" height="6" rx="1" />
    <rect x="11" y="3" width="6" height="6" rx="1" />
    <rect x="3" y="11" width="6" height="6" rx="1" />
    <rect x="11" y="11" width="6" height="6" rx="1" />
  </svg>
);

export const ListIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M4 6h12M4 10h12M4 14h12" />
  </svg>
);

export const FileIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M5 3h7l4 4v11H5V3z" />
    <path d="M12 3v4h4" />
  </svg>
);

export const NotesIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M4 4h12v9l-3 3H4V4z" />
    <path d="M7 8h6M7 11h4" />
  </svg>
);

export const ClockIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <circle cx="10" cy="10" r="7" />
    <path d="M10 6v4l3 2" />
  </svg>
);

export const ChevronIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M7 5l6 5-6 5" />
  </svg>
);

export const CloseIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" className={className}>
    <path d="M5 5l10 10M15 5L5 15" />
  </svg>
);

export const CheckIcon = ({ size = 16, className }: IconProps) => (
  <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M4 10l4 4 8-8" />
  </svg>
);