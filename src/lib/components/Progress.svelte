<script lang="ts">
  import { onMount } from "svelte";
  import { fade } from "svelte/transition";

  import type { ExpansionProgress } from "$lib/stores/progressStore";
  import { progress } from "$lib/stores/progressStore";
  import { isMobile } from "$lib/utils";

  let progressData: Record<string, ExpansionProgress> = {};
  let totalCompleted = 0;
  let totalQuests = 0;
  let totalPercent = 0;
  let showRainbow = false;
  let showExpanded = false;
  let isHovering = false;
  let hoverTimeout: ReturnType<typeof setTimeout> | null = null;
  let mobile = false;

  function handleBarInteraction(e: MouseEvent | KeyboardEvent) {
    if (e instanceof KeyboardEvent && e.key !== "Enter" && e.key !== " ")
      return;

    if (mobile) {
      showExpanded = !showExpanded;
    } else {
      showRainbow = !showRainbow;
    }
  }

  function handleBarMouseEnter() {
    if (mobile) return;

    isHovering = true;
    hoverTimeout = setTimeout(() => {
      showExpanded = true;
    }, 1000);
  }

  function handleBarMouseLeave() {
    if (mobile) return;

    isHovering = false;
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      hoverTimeout = null;
    }
    showExpanded = false;
  }

  onMount(() => {
    mobile = isMobile();

    progress.subscribe((value) => {
      progressData = value;

      totalCompleted = Object.values(value).reduce(
        (sum, exp) => sum + exp.completed,
        0
      );
      totalQuests = Object.values(value).reduce(
        (sum, exp) => sum + exp.total,
        0
      );
      totalPercent =
        totalQuests > 0 ? Math.round((totalCompleted / totalQuests) * 100) : 0;
    });
  });
</script>

<!-- Total Progress Bar (Rainbow) -->
<div
  transition:fade
  class="mb-4 bg-white rounded-lg p-4 shadow progress-container"
  role="region"
  aria-label="Progress statistics"
>
  {#if mobile}
    <button
      class="w-full font-semibold text-gray-700 text-center cursor-pointer active:opacity-70"
      on:click={handleBarInteraction}
    >
      FINAL FANTASY XIV
      <span class="inline sm:hidden ml-1">({totalCompleted}/{totalQuests})</span
      >
    </button>
  {:else}
    <p class="font-semibold text-gray-700 text-center">FINAL FANTASY XIV</p>
  {/if}

  <!-- Total Progress Bar -->
  <div
    class="hidden sm:block w-full bg-gray-200 rounded-full h-5 relative overflow-hidden shadow-inner cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 {isHovering
      ? 'hovering-outline'
      : ''}"
    role="button"
    tabindex="0"
    title={mobile
      ? "Click to expand details"
      : "Hover and wait to show expansions"}
    aria-label={mobile
      ? "Click to expand details"
      : "Click to toggle rainbow, hover to expand details"}
    on:click={handleBarInteraction}
    on:keydown={handleBarInteraction}
    on:mouseenter={handleBarMouseEnter}
    on:mouseleave={handleBarMouseLeave}
  >
    <div
      class="{showRainbow
        ? 'rainbow-bar'
        : 'blue-bar'} h-full rounded-full transition-colors duration-300"
      style="width: {totalPercent}%"
    ></div>
    <p
      class="absolute w-full text-center text-sm font-semibold top-1/2 left-0 -translate-y-1/2 text-white pointer-events-none"
    >
      {totalCompleted}/{totalQuests} ({totalPercent}%)
    </p>
  </div>

  <!-- Expansion Progress Bars (shown on hover) -->
  <div
    class="{showExpanded
      ? 'grid'
      : 'hidden'} sm:grid-cols-1 md:grid-cols-2 gap-4 mt-4 transition-all duration-300"
  >
    {#each Object.entries(progressData) as [name, { completed, total, percent }] (name)}
      <div class="flex flex-col items-center">
        <!-- Expansion Name -->
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
</div>

<style>
  @keyframes blink-outline {
    0%,
    100% {
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.3);
    }
    50% {
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.7);
    }
  }

  .hovering-outline {
    animation: blink-outline 1s ease-in-out infinite;
  }

  .blue-bar {
    background: linear-gradient(90deg, #3b82f6, #2563eb, #1d4ed8);
  }

  .rainbow-bar {
    background: linear-gradient(
      90deg,
      #ffb3ba 0%,
      #ffdfba 10%,
      #ffffba 20%,
      #baffc9 30%,
      #bae1ff 40%,
      #d4baff 50%,
      #ffb3f0 60%,
      #ffb3ba 70%,
      #ffdfba 80%,
      #ffffba 90%,
      #baffc9 100%
    );
  }
</style>
