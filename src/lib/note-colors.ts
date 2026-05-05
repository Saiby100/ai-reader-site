type NoteColorDef = {
  /** CSS variable for the accent/border color */
  border: string;
  /** CSS variable for the light background */
  bg: string;
  /** Tailwind class for the color dot selector */
  dot: string;
};

/** Mapping from color name to design-system variables */
export const NOTE_COLORS: Record<string, NoteColorDef> = {
  amber: { border: 'var(--amber)', bg: 'var(--amber-light)', dot: 'bg-amber' },
  accent: { border: 'var(--accent)', bg: 'var(--accent-light)', dot: 'bg-accent' },
  green: { border: 'var(--green)', bg: 'var(--green-light)', dot: 'bg-green' },
};

/** Ordered list of available color names */
export const NOTE_COLOR_NAMES = Object.keys(NOTE_COLORS);

/** Default color for new notes */
export const DEFAULT_NOTE_COLOR = 'amber';