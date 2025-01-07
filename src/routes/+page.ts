// The app is static client-side only
export const ssr = false;
export const prerender = true;

import { base } from "$app/paths";
import type { ExpansionsQuests } from "$lib/model.js";
export async function load({ fetch }): Promise<{ quests: ExpansionsQuests }> {
  const response = await fetch(`${base}/Quests.json`);
  if (!response.ok) {
    throw new Error("Failed to fetch quests");
  }
  const data = await response.json();
  return {
    quests: data,
  };
}
