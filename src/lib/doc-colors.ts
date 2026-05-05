export type DocColor = 'accent' | 'green' | 'amber' | 'rose';

type ColorSet = {
  /** Spine/primary color CSS variable */
  spine: string;
  /** Light background CSS variable */
  light: string;
  /** Text color CSS variable */
  text: string;
};

const COLOR_MAP: Record<DocColor, ColorSet> = {
  accent: { spine: 'var(--accent)', light: 'var(--accent-light)', text: 'var(--accent)' },
  green: { spine: 'var(--green)', light: 'var(--green-light)', text: 'var(--green)' },
  amber: { spine: 'var(--amber)', light: 'var(--amber-light)', text: 'var(--amber)' },
  rose: { spine: 'var(--rose)', light: 'var(--rose-light)', text: 'var(--rose)' },
};

const COLORS: DocColor[] = ['accent', 'green', 'amber', 'rose'];

export const getColorSet = (color: DocColor): ColorSet => COLOR_MAP[color];

export const getColorForIndex = (index: number): DocColor => COLORS[index % COLORS.length];