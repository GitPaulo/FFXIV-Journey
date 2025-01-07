import { writable, get } from "svelte/store";
import type { ExpansionsQuests, Quest } from "$lib/model";
import { initAllExpansionProgress } from "./progressStore";

const LOCAL_STORAGE_KEY = "ffxiv-journey:completed";

// Store definitions
export const quests = writable<ExpansionsQuests>([]);
export const filteredQuests = writable<ExpansionsQuests>([]);
export const completedQuests = writable<Record<number, boolean>>(
  (() => {
    try {
      return JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || "{}") || {};
    } catch {
      console.warn(`Invalid data in localStorage for key ${LOCAL_STORAGE_KEY}`);
      return {};
    }
  })()
);
export const isLoadingQuests = writable<boolean>(true);
export const currentExpansion = writable<string>("");

// Utility to persist completed quests to localStorage
export function storeCompletedQuests() {
  try {
    localStorage.setItem(
      LOCAL_STORAGE_KEY,
      JSON.stringify(get(completedQuests))
    );
  } catch (error) {
    console.error("Failed to store completed quests in localStorage:", error);
  }
}

// Helper to get a flat list of all quests
function getAllQuests(): Quest[] {
  return get(quests).flatMap((expansion) =>
    Object.values(expansion.quests).flat()
  );
}

// Update completion status for a quest and subsequent quests
export function setQuestCompletion(quest: Quest, isChecked: boolean) {
  const questId = quest["#"];
  let reachedTarget = false;

  completedQuests.update((current) => {
    const updatedQuests = { ...current };

    getAllQuests().forEach((q) => {
      if (!reachedTarget) {
        // For checking: check all quests up to the target quest
        // For unchecking: leave previous quests unchanged
        updatedQuests[q["#"]] = isChecked || updatedQuests[q["#"]];
      }

      if (q["#"] === questId) {
        reachedTarget = true;
        // Explicitly set the target quest based on the current action
        updatedQuests[q["#"]] = isChecked;
      }

      if (reachedTarget && !isChecked) {
        // Only uncheck quests from the target onward
        updatedQuests[q["#"]] = false;
      }
    });

    return updatedQuests;
  });

  storeCompletedQuests();
  initAllExpansionProgress();
  updateCurrentExpansion();
}

// Update completion status for a single quest
export function setSingleQuestCompletion(quest: Quest, isChecked: boolean) {
  const questId = quest["#"];

  completedQuests.update((current) => ({
    ...current,
    [questId]: isChecked,
  }));

  storeCompletedQuests();
  initAllExpansionProgress();
  updateCurrentExpansion();
}

// Update the current expansion based on the last completed quest
export function updateCurrentExpansion() {
  const completed = get(completedQuests);

  const lastCompletedExpansion = get(quests).reduce<string | null>(
    (last, expansion) => {
      const hasCompletedQuest = Object.values(expansion.quests)
        .flat()
        .some((quest) => completed[quest["#"]]);
      return hasCompletedQuest ? expansion.name : last;
    },
    null
  );

  if (lastCompletedExpansion) {
    currentExpansion.set(lastCompletedExpansion);
  }
}

// Get the last checked quest
export function getLastCheckedQuest(): Quest | null {
  const completed = get(completedQuests);

  return getAllQuests().reduce<Quest | null>(
    (lastChecked, quest) => (completed[quest["#"]] ? quest : lastChecked),
    null
  );
}
