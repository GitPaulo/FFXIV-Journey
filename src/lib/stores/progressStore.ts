import { writable, get } from "svelte/store";
import {
  quests,
  completedQuests,
  currentExpansion,
} from "$lib/stores/questsStore";
import { openModal } from "$lib/stores/modalManager";
import { encode, decode } from "@msgpack/msgpack";

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

export type SharableState = {
  completedQuests: string[];
  currentExpansion: string;
};

function toBase64Url(base64: string): string {
  return base64.replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromBase64Url(base64Url: string): string {
  return (
    base64Url.replace(/-/g, "+").replace(/_/g, "/") +
    "=".repeat((4 - (base64Url.length % 4)) % 4)
  );
}

// Compress and encode state into a sharable string
export async function compressAndEncode(state: SharableState): Promise<{
  base64Encoded: string;
  basePath: string;
}> {
  // Step 1: Optimize "completedQuests" using Delta Encoding
  const optimizedCompletedQuests = convertToDeltas(state.completedQuests);

  // Create optimized state
  const optimizedState = {
    cq: optimizedCompletedQuests, // Delta encoded completed quests
    ce: state.currentExpansion, // Expansion name remains a string
  };

  // Step 2: Serialize using MessagePack
  const binaryState = encode(optimizedState);

  // Step 3: Compress using the native Gzip CompressionStream
  const stream = new CompressionStream("gzip");
  const writer = stream.writable.getWriter();
  writer.write(binaryState);
  writer.close();

  const compressed = await new Response(stream.readable).arrayBuffer();

  // Step 4: Convert to Base64 URL-safe format
  const base64Encoded = toBase64Url(
    btoa(String.fromCharCode(...new Uint8Array(compressed)))
  );

  // Create the base URL
  const basePath =
    window.location.origin + window.location.pathname.replace(/\/$/, "");

  return { base64Encoded, basePath };
}

// Decode and decompress a shared progress string into the original state
export async function decodeAndDecompress(
  base64Encoded: string
): Promise<SharableState> {
  // Step 1: Decode Base64 URL-safe back to a Uint8Array
  const binaryString = atob(fromBase64Url(base64Encoded));
  const compressed = Uint8Array.from(binaryString, (char) =>
    char.charCodeAt(0)
  );

  // Step 2: Decompress using the native Gzip DecompressionStream
  const stream = new DecompressionStream("gzip");
  const writer = stream.writable.getWriter();
  writer.write(compressed);
  writer.close();

  const decompressed = await new Response(stream.readable).arrayBuffer();

  // Step 3: Deserialize using MessagePack
  const optimizedState = decode(new Uint8Array(decompressed)) as {
    cq: number[]; // Delta-encoded quest IDs
    ce: string; // Expansion name
  };

  // Step 4: Reconstruct original "completedQuests" using Delta Decoding
  const completedQuests = convertFromDeltas(optimizedState.cq);

  return {
    completedQuests,
    currentExpansion: optimizedState.ce,
  };
}

// Convert array of IDs to delta encoding
function convertToDeltas(ids: string[]): number[] {
  const numbers = ids.map(Number).sort((a, b) => a - b);

  if (numbers.length === 0) return [];
  const deltas: number[] = [numbers[0]];

  // Calculate the difference (delta) between consecutive IDs
  for (let i = 1; i < numbers.length; i++) {
    deltas.push(numbers[i] - numbers[i - 1]);
  }

  /*
    Example:
    Input IDs (sorted): [65564, 65565, 65567, 65570]
    
    ASCII Representation:
      IDs:     65564   65565       65567          65570
      Deltas:   +0       +1         +2             +3
    
    Output Deltas: [65564, 1, 2, 3]
    - First ID is stored as is: 65564
    - 65565 - 65564 = 1 (delta from previous)
    - 65567 - 65565 = 2
    - 65570 - 65567 = 3
  */

  return deltas;
}

// Convert delta-encoded array back to original IDs
function convertFromDeltas(deltas: number[]): string[] {
  if (deltas.length === 0) return [];

  const ids: number[] = [deltas[0]];
  for (let i = 1; i < deltas.length; i++) {
    ids.push(ids[i - 1] + deltas[i]);
  }

  /*
    Example:
    Input Deltas: [65564, 1, 2, 3]
    
    ASCII Representation:
      Base:     65564   +1        +2          +3
      IDs:      65564   65565     65567       65570

    Output IDs: [65564, 65565, 65567, 65570]
    - Start with the base ID: 65564
    - Add 1: 65564 + 1 = 65565
    - Add 2: 65565 + 2 = 65567
    - Add 3: 65567 + 3 = 65570
  */

  return ids.map(String);
}

// Svelte store for overall progress
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
export function initAllExpansionProgress(): void {
  const allQuests = get(quests);
  if (!allQuests.length) return;

  const updatedProgress: Record<string, ExpansionProgress> = {};
  const updatedGroupProgress: Record<
    string,
    Record<string, QuestGroupProgress>
  > = {};

  allQuests.forEach((expansion) => {
    updatedProgress[expansion.name] = calculateExpansionProgress(
      expansion.name
    );

    updatedGroupProgress[expansion.name] = {};

    Object.keys(expansion.quests).forEach((questGroup) => {
      updatedGroupProgress[expansion.name][questGroup] =
        calculateQuestGroupProgress(expansion.name, questGroup);
    });
  });

  progress.set(updatedProgress);
  groupProgress.set(updatedGroupProgress);
}

// Parse shared progress from URL
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

// Load shared progress from URL and apply it
export async function loadSharedProgress(): Promise<void> {
  const compressedState = getSharedProgress();
  if (!compressedState) return;

  openModal(
    "Shared Progress",
    "You are viewing a shared progress link. Your progress won't be overwritten without prompt.",
    () => {},
    () => {
      window.location.href = window.location.origin + window.location.pathname;
    },
    "Understood",
    "",
    false
  );

  try {
    const state = await decodeAndDecompress(compressedState);
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

// Generate a shareable progress link
export async function generateShareableLink(): Promise<void> {
  const completed = get(completedQuests);
  const completedIds = Object.keys(completed).filter(
    (id) => completed[Number(id)]
  );

  const state: SharableState = {
    completedQuests: completedIds,
    currentExpansion: get(currentExpansion),
  };

  try {
    const { base64Encoded, basePath } = await compressAndEncode(state);
    const shareableLink = `${basePath}?progress=${base64Encoded}`;

    await navigator.clipboard.writeText(shareableLink);
    openModal(
      "Shareable Link",
      "The progress link has been copied to your clipboard. Share it with your friends!",
      () => {},
      () => {},
      "Understood",
      "",
      false
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
