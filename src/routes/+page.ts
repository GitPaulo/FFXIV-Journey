export const ssr = false
export const prerender = true

import { base } from '$app/paths';
import type { ExpansionsQuests } from '$lib/model.js';

export type QuestsState = {
  loading: boolean;
  quests: Promise<ExpansionsQuests>;
};

export async function load({ fetch }): Promise<QuestsState> {
  return {
    loading: true,
    // TODO: There is 100% a better way to do this but I'm new to sveltekit
    quests: fetch(`${base}/Quests.json`).then(async (response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch quests: ${response.status}`);
      }
      return await response.json();
    }),
  };
}
