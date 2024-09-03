/**
 * Sanitize FFXIV Mark-up into a human-readable string
 * @param str The string to sanitize
 * @returns string
 */
export function sanitizeFFXIVMarkUp(str: string | null): string {
  return str
    ? str.replace(/<[^>]*>/g, "")
    : "This quest has no description.";
}

/**
 * Returns the Garland Tools URL for a given quest.
 * @param questId The unique ID of the quest.
 * @returns The URL to the quest on Garland Tools.
 */
export function getGarlandToolsQuestURLByID(questId: number): string {
  return `https://www.garlandtools.org/db/#quest/${questId}`;
}
