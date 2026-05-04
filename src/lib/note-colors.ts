/** Mapping from color name to Tailwind background classes */
export const NOTE_COLORS: Record<string, { /** Class for the accent bar */ accent: string; /** Class for the selector dot */ dot: string }> = {
  yellow: { accent: 'bg-yellow-300', dot: 'bg-yellow-400' },
  blue: { accent: 'bg-blue-300', dot: 'bg-blue-400' },
  green: { accent: 'bg-green-300', dot: 'bg-green-400' },
  pink: { accent: 'bg-pink-300', dot: 'bg-pink-400' },
  purple: { accent: 'bg-purple-300', dot: 'bg-purple-400' },
};

/** Ordered list of available color names */
export const NOTE_COLOR_NAMES = Object.keys(NOTE_COLORS);

/** Default color for new notes */
export const DEFAULT_NOTE_COLOR = 'yellow';