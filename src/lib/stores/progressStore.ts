import { writable, get } from "svelte/store";
import { quests, completedQuests } from "$lib/stores/questsStore";
import type { ExpansionProgress } from "$lib/stores/questsStore";

// Store for overall progress
export const progress = writable<Record<string, ExpansionProgress>>({});

// Function to calculate progress for a single expansion
export function calculateExpansionProgress(expansionName: string) {
  const $quests = get(quests);
  if (!$quests.length) return { percent: 0, completed: 0, total: 0 };

  const expansion = $quests.find((exp) => exp.name === expansionName);
  if (!expansion) return { percent: 0, completed: 0, total: 0 };

  const questsArray = Object.values(expansion.quests).flat();
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

// Function to calculate progress for all expansions
export function calculateAllProgress() {
  const $quests = get(quests);
  if (!$quests.length) return;

  const newProgress: Record<string, ExpansionProgress> = {};
  for (const expansion of $quests) {
    newProgress[expansion.name] = calculateExpansionProgress(expansion.name);
  }

  progress.set(newProgress);
}
