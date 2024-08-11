export const ssr = false
export const prerender = true

import { base } from '$app/paths';

export async function load({ fetch }) {
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