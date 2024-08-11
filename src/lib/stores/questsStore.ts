import { writable, get } from "svelte/store";
import type { Quests, Quest } from "$lib/model";

const LOCAL_STORAGE_KEY = "ffxiv-journey:completed";

// Store for quests
export const quests = writable<Quests>([]);
export const filteredQuests = writable<Quests>([]);
export const completedQuests = writable<Record<number, boolean>>(
  JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || "{}")
);
export const progress = writable<Record<string, { percent: number; completed: number; total: number }>>({});
export const loading = writable<boolean>(true);
export const currentExpansion = writable<string>("");

export function saveCompletedQuests() {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(get(completedQuests)));
}

export function calculateProgress(expansionName: string) {
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
  const newProgress: Record<string, { percent: number; completed: number; total: number }> = {};

  for (const expansion of $quests) {
    newProgress[expansion.name] = calculateProgress(expansion.name);
  }

  progress.set(newProgress);
}

export function toggleQuestCompletion(quest: Quest, isChecked: boolean) {
  const $quests = get(quests);
  const questIds: number[] = Object.values($quests)
    .flat()
    .map((q: any) => q["#"]);

  let questFound = false;

  for (let i = 0; i < questIds.length; i++) {
    if (questFound) {
      // Uncheck all quests after the found quest
      completedQuests.update((current) => {
        current[questIds[i]] = false;
        return current;
      });
    } else {
      // Check all quests leading up to and including the found quest
      completedQuests.update((current) => {
        current[questIds[i]] = true;
        return current;
      });
    }

    if (questIds[i] === quest["#"]) {
      questFound = true;

      // If the current quest is unchecked, uncheck it and uncheck all following quests
      if (!isChecked) {
        completedQuests.update((current) => {
          current[questIds[i]] = false;
          return current;
        });
      }
    }
  }

  saveCompletedQuests();
  calculateAllProgress();
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
