import { writable, get } from "svelte/store";
import {
  compressToEncodedURIComponent,
  decompressFromEncodedURIComponent,
} from "lz-string";
import {
  quests,
  completedQuests,
  currentExpansion,
} from "$lib/stores/questsStore";
import { openModal } from "$lib/stores/modalManager";

export type ExpansionProgress = {
  percent: number;
  completed: number;
  total: number;
};

export type QuestGroupProgress = {
  percent: number;
  completed: number;
  total: number;
};

// Store for overall progress
export const progress = writable<Record<string, ExpansionProgress>>({});
export const groupProgress = writable<
  Record<string, Record<string, QuestGroupProgress>>
>({});

// Calculate progress for a single expansion
export function calculateExpansionProgress(
  expansionName: string
): ExpansionProgress {
  const allQuests = get(quests);
  if (!allQuests.length) return { percent: 0, completed: 0, total: 0 };

  const expansion = allQuests.find((exp) => exp.name === expansionName);
  if (!expansion) return { percent: 0, completed: 0, total: 0 };

  const questsArray = Object.values(expansion.quests).flat();
  const totalQuests = questsArray.length;
  const completedCount = questsArray.filter(
    (quest) => get(completedQuests)[quest["#"]]
  ).length;

  return {
    percent:
      totalQuests > 0 ? Math.floor((completedCount / totalQuests) * 100) : 0,
    completed: completedCount,
    total: totalQuests,
  };
}

// Calculate progress for a single quest group within an expansion
export function calculateQuestGroupProgress(
  expansionName: string,
  questGroup: string
): QuestGroupProgress {
  const allQuests = get(quests);
  if (!allQuests.length) {
    return { percent: 0, completed: 0, total: 0 };
  }

  const expansion = allQuests.find((exp) => exp.name === expansionName);
  if (!expansion || !expansion.quests[questGroup]) {
    return { percent: 0, completed: 0, total: 0 };
  }

  const questsArray = expansion.quests[questGroup];
  const totalQuests = questsArray.length;
  const completedCount = questsArray.reduce(
    (count, quest) => count + (get(completedQuests)[quest["#"]] ? 1 : 0),
    0
  );

  return {
    percent:
      totalQuests > 0 ? Math.floor((completedCount / totalQuests) * 100) : 0,
    completed: completedCount,
    total: totalQuests,
  };
}

// Initialize all expansion and quest group progress
export function initAllExpansionProgress() {
  const allQuests = get(quests);
  if (!allQuests.length) return;

  const updatedProgress: Record<string, ExpansionProgress> = {};
  const updatedGroupProgress: Record<
    string,
    Record<string, QuestGroupProgress>
  > = {};

  allQuests.forEach((expansion) => {
    // Calculate expansion progress
    updatedProgress[expansion.name] = calculateExpansionProgress(
      expansion.name
    );

    // Initialize nested object for this expansion
    updatedGroupProgress[expansion.name] = {};

    // Calculate progress for each quest group
    Object.keys(expansion.quests).forEach((questGroup) => {
      updatedGroupProgress[expansion.name][questGroup] =
        calculateQuestGroupProgress(expansion.name, questGroup);
    });
  });

  progress.set(updatedProgress);
  groupProgress.set(updatedGroupProgress);
}

// Get shared progress from URL
export function getSharedProgress(): string {
  try {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get("progress") || "";
  } catch {
    console.warn("Failed to parse shared progress from URL.");
    return "";
  }
}

// Check if shared progress exists
export function hasSharedProgress(): boolean {
  return !!getSharedProgress();
}

// Load shared progress from URL
export function loadSharedProgress() {
  const compressedState = getSharedProgress();

  if (compressedState) {
    openModal(
      "Shared Progress",
      "You are viewing a shared progress link. Your progress won't be overwritten without prompt.",
      () => {},
      () => {
        window.location.href =
          window.location.origin + window.location.pathname;
      },
      "Understood",
      "",
      false
    );

    try {
      const state = JSON.parse(
        decompressFromEncodedURIComponent(compressedState) || "{}"
      );

      const reconstructedCompleted: Record<number, boolean> = {};
      state.completedQuests.forEach((id: string) => {
        reconstructedCompleted[Number(id)] = true;
      });

      completedQuests.set(reconstructedCompleted);
      currentExpansion.set(state.currentExpansion);
    } catch (error) {
      console.error("Failed to decode shared progress:", error);
    }
  }
}

// Generate a shareable link for progress
export function generateShareableLink() {
  const completed = get(completedQuests);
  const completedIds = Object.keys(completed).filter(
    (id) => completed[Number(id)]
  );

  const state = {
    completedQuests: completedIds,
    currentExpansion: get(currentExpansion),
  };

  try {
    const compressedState = compressToEncodedURIComponent(
      JSON.stringify(state)
    );
    const basePath =
      window.location.origin + window.location.pathname.replace(/\/$/, "");
    const shareableLink = `${basePath}?progress=${compressedState}`;

    navigator.clipboard
      .writeText(shareableLink)
      .then(() =>
        openModal(
          "Shareable Link",
          "The progress link has been copied to your clipboard. Share it with your friends!",
          () => {},
          () => {},
          "Understood",
          "",
          false
        )
      )
      .catch(() =>
        openModal(
          "Shareable Link",
          "Failed to copy the progress link to your clipboard. Please try again.",
          () => {},
          () => {},
          "Understood",
          "",
          false
        )
      );
  } catch (error) {
    console.error("Failed to generate shareable link:", error);
    openModal(
      "Shareable Link",
      "An error occurred while generating the progress link. Please try again later.",
      () => {},
      () => {},
      "Understood",
      "",
      false
    );
  }
}
