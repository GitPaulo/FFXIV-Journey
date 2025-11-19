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
  let isPinned = false;

  function handleBarClick() {
    if (mobile) {
      showExpanded = !showExpanded;
    } else {
      isPinned = !isPinned;
      if (isPinned) showExpanded = true;
    }
  }

  function handleBarDoubleClick() {
    if (!mobile) showRainbow = !showRainbow;
  }

  function handleBarMouseEnter() {
    if (mobile) return;
    isHovering = true;
    hoverTimeout = setTimeout(() => {
      showExpanded = true;
    }, 1000);
  }

  function handleBarMouseLeave() {
    if (mobile || isPinned) return;
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
      on:click={handleBarClick}
    >
      FINAL FANTASY XIV
      <span class="inline sm:hidden ml-1">({totalCompleted}/{totalQuests})</span
      >
    </button>
  {:else}
    <p
      class="font-semibold text-gray-700 text-center flex items-center justify-center gap-2"
    >
      FINAL FANTASY XIV
      {#if showExpanded}
        <svg
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          class="{isPinned
            ? 'text-blue-500'
            : 'text-gray-800'} transition-colors duration-300"
        >
          <path
            d="M19.1835 7.80516L16.2188 4.83755C14.1921 2.8089 13.1788 1.79457 12.0904 2.03468C11.0021 2.2748 10.5086 3.62155 9.5217 6.31506L8.85373 8.1381C8.59063 8.85617 8.45908 9.2152 8.22239 9.49292C8.11619 9.61754 7.99536 9.72887 7.86251 9.82451C7.56644 10.0377 7.19811 10.1392 6.46145 10.3423C4.80107 10.8 3.97088 11.0289 3.65804 11.5721C3.5228 11.8069 3.45242 12.0735 3.45413 12.3446C3.45809 12.9715 4.06698 13.581 5.28476 14.8L6.69935 16.2163L2.22345 20.6964C1.92552 20.9946 1.92552 21.4782 2.22345 21.7764C2.52138 22.0746 3.00443 22.0746 3.30236 21.7764L7.77841 17.2961L9.24441 18.7635C10.4699 19.9902 11.0827 20.6036 11.7134 20.6045C11.9792 20.6049 12.2404 20.5358 12.4713 20.4041C13.0192 20.0914 13.2493 19.2551 13.7095 17.5825C13.9119 16.8472 14.013 16.4795 14.2254 16.1835C14.3184 16.054 14.4262 15.9358 14.5468 15.8314C14.8221 15.593 15.1788 15.459 15.8922 15.191L17.7362 14.4981C20.4 13.4973 21.7319 12.9969 21.9667 11.9115C22.2014 10.826 21.1954 9.81905 19.1835 7.80516Z"
            fill="currentColor"
          />
        </svg>
      {/if}
    </p>
  {/if}

  <!-- Total Progress Bar -->
  <div
    class="hidden sm:block w-full bg-gray-200 rounded-full h-5 relative overflow-hidden shadow-inner cursor-pointer focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300 {isHovering
      ? 'hovering-outline'
      : ''}"
    role="button"
    tabindex="0"
    title={mobile ? "Click to expand" : "Hold and wait to show or click to pin"}
    aria-label={mobile
      ? "Click to expand details"
      : "Hold to show progress and click to pin"}
    on:click={handleBarClick}
    on:keydown={(e) => e.key === "Enter" && handleBarClick()}
    on:dblclick={handleBarDoubleClick}
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
  {#if showExpanded}
    <div
      class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 transition-all duration-300"
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
  {/if}
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
