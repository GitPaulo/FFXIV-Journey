/**
 * Unlock model
 */
export interface Unlock {
  Name: string;            // Name of the unlock
  Image: string;           // Path to the unlock image
  ContentTypeID: number;   // Content type ID
  ContentTypeName: string; // Content type name
}

/**
 * Quest model
 */
export type Quest = {
  "#": number;                // Unique identifier for the quest
  Id: string;                 // Quest identifier string
  Name: string;               // Name of the quest
  Description: string | null; // Description of the quest
  ExpansionName: string;      // Expansion name
  EventIconType: number;      // Event icon type, representing the type of quest (3 for MSQ)
  PreviousQuests: number[];   // Array containing up to 4 previous quest IDs
  NextMSQ: number | null;     // ID of the next MSQ quest or null if the last MSQ quest
  QuestGroup: string | null;  // Starting location or null if not applicable
  Image: string | null;       // Path to the quest image or null if not available
  Unlocks: Unlock[];          // Array of unlocks
};

/**
 * Grouped quests model
 */
export type Quests = {
  [group: string]: Quest[]; // Key-value pairs of groups and their quests
};

/**
 * Expansion model
 */
export type Expansion = {
  name: string;  // Name of the expansion
  quests: Quests;// Quests grouped by location or type
};

/**
 * Expansions quests array
 */
export type ExpansionsQuests = Array<Expansion>; // Array of expansions and their quests
