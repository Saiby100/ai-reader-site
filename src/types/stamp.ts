/** Represents a user action stamp with actor and time */
export type Stamp = {
  /** The user who performed the action */
  user: {
    /** Unique user identifier */
    id: string;
    /** Display name of the user */
    name: string;
  };
  /** When the action occurred */
  timestamp: Date;
};
