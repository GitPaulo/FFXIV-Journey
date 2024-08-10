/**
 * Quest model
 */

export type Quest = {
  "#": number; // Unique identifier for the quest
  Id: string; // Quest identifier string
  Name: string; // Name of the quest
  Expansion: "A Realm Reborn" | "Heavensward" | "Stormblood" | "Shadowbringers" | "Endwalker" | "Dawntrail"; // Expansion name
  EventIconType: number; // Event icon type, representing the type of quest (3 for MSQ)
  PreviousQuests: number[]; // Array containing up to 4 previous quest IDs
  NextMSQ: number | null; // ID of the next MSQ quest or null if none
  StartingLocation: "Gridania" | "Limsa Lominsa" | "Ul'dah" | null; // Starting location or null if not applicable
  Image: string | null; // Path to the quest image or null if not available
};

export type Quests = Array<{
  name: string;
  quests: {
    [location: string]: Quest[];
  };
}>;

