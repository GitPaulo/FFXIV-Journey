<script lang="ts">
  import { progress } from "$lib/stores/progressStore";
  import type { ExpansionProgress } from "$lib/stores/questsStore";
  import { onMount } from "svelte";

  let progressData: Record<string, ExpansionProgress> = {};

  // Initialize progress data on component mount
  onMount(() => {
    progress.subscribe((value) => {
      progressData = value;
    });
  });
</script>

<div
  class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg p-4 shadow"
>
  {#each Object.entries(progressData) as [name, { completed, total, percent }] (name)}
    <div class="flex flex-col items-center">
      <!-- Expansion Name with Progress Stats -->
      <p class="font-semibold text-gray-700">
        {name}
        <span class="inline sm:hidden ml-1">({completed}/{total})</span>
      </p>

      <!-- Progress Bar -->
      <div
        class="hidden sm:block w-full bg-gray-200 rounded-full h-4 relative overflow-hidden shadow-inner"
      >
        <div
          class="h-full rounded-full bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 transition-all duration-700 ease-in-out"
          style="width: {percent}%"
        ></div>
        <p
          class="absolute w-full text-center text-xs font-semibold top-0 left-0 text-white"
        >
          {completed}/{total} ({percent}%)
        </p>
      </div>
    </div>
  {/each}
</div>
