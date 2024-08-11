import { writable, get } from "svelte/store";
import type { ExpansionsQuests, Quest } from "$lib/model";

const LOCAL_STORAGE_KEY = "ffxiv-journey:completed";

// Types
export type ExpansionProgress = { percent: number; completed: number; total: number }

// Store for quests
export const quests = writable<ExpansionsQuests>([]);
export const filteredQuests = writable<ExpansionsQuests>([]);
export const completedQuests = writable<Record<number, boolean>>(
  JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || "{}")
);
export const progress = writable<Record<string, ExpansionProgress>>({});
export const loading = writable<boolean>(true);
export const currentExpansion = writable<string>("");

export function storeCompletedQuests() {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(get(completedQuests)));
}

export function CalculateExpansionProgress(expansionName: string) {
  const $quests = get(quests);
  const expansion = $quests.find((exp) => exp.name === expansionName);
  if (!expansion) return { percent: 0, completed: 0, total: 0 };

  const questsArray: Quest[] = Object.values(expansion.quests).flat();
  const totalQuests = questsArray.length;
  const completedQuestsCount = questsArray.filter(
    (quest) => get(completedQuests)[quest["#"]]
  ).length;

  const percent =
    totalQuests > 0
      ? Math.floor((completedQuestsCount / totalQuests) * 100)
      : 0;

  return {
    percent,
    completed: completedQuestsCount,
    total: totalQuests,
  };
}

export function calculateAllProgress() {
  const $quests = get(quests);
  const newProgress: Record<string, ExpansionProgress> = {};

  for (const expansion of $quests) {
    newProgress[expansion.name] = CalculateExpansionProgress(expansion.name);
  }

  progress.set(newProgress);
}

export function toggleQuestCompletion(quest: Quest, isChecked: boolean) {
  const $quests = get(quests);

  let questFound = false;

  for (const expansion of $quests) {
    const questIds = Object.values(expansion.quests)
      .flat()
      .map((q: Quest) => q["#"]);

    completedQuests.update((current) => {
      const newCompletedQuests = { ...current };

      for (let i = 0; i < questIds.length; i++) {
        if (questFound) {
          // Uncheck all quests after the found quest
          newCompletedQuests[questIds[i]] = false;
        } else {
          // Check all quests leading up to and including the found quest
          newCompletedQuests[questIds[i]] = true;
        }

        if (questIds[i] === quest["#"]) {
          questFound = true;

          // If the current quest is unchecked, uncheck it and uncheck all following quests
          if (!isChecked) {
            newCompletedQuests[questIds[i]] = false;
          }
        }
      }

      return newCompletedQuests; // Return a new object to trigger reactivity
    });
  }

  storeCompletedQuests();
  calculateAllProgress();
  updateCurrentExpansion();
}

export function updateCurrentExpansion() {
  const $quests = get(quests);
  let lastCompletedQuestId: number | null = null;
  let lastCompletedExpansion: string | null = null;

  for (const expansion of $quests) {
    for (const location in expansion.quests) {
      for (const quest of expansion.quests[location]) {
        if (get(completedQuests)[quest["#"]]) {
          lastCompletedQuestId = quest["#"];
          lastCompletedExpansion = expansion.name;
        }
      }
    }
  }

  if (lastCompletedExpansion) {
    currentExpansion.set(lastCompletedExpansion);
  }
}
