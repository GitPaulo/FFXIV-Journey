<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { slide } from "svelte/transition";
  import {
    autoMode,
    toggleAutoMode,
    showScrollToTop,
  } from "$lib/stores/actionBarStore";
  import Tooltip from "./Tooltip.svelte";

  const dispatch = createEventDispatcher();

  function onShareProgressClicked() {
    dispatch("generateLink");
  }

  function onScrollToTopClicked() {
    dispatch("scrollToTop");
  }

  function onScrollToLastQuestClicked() {
    dispatch("scrollToLastQuest");
  }

  let tooltipTarget: HTMLElement | null = null;

  export let lastCheckedQuestId: number | null = null;
</script>

<div
  transition:slide
  id="action-bar"
  class="fixed md:absolute top-1 sm:top-2 mt-2 bg-white rounded-lg p-1 sm:p-2 shadow flex items-center justify-between z-50"
>
  <!-- Toggle Button -->
  <div bind:this={tooltipTarget} class="flex items-center">
    <button
      on:click={toggleAutoMode}
      class={`w-10 h-5 sm:w-12 sm:h-6 flex items-center rounded-full p-1 transition-colors duration-300 ${
        $autoMode ? "bg-gray-300" : "bg-blue-500"
      }`}
    >
      <div
        class={`h-3.5 w-3.5 sm:h-4 sm:w-4 rounded-full bg-white shadow-md transform transition-transform duration-300 ${
          $autoMode ? "translate-x-0" : "translate-x-5 sm:translate-x-6"
        }`}
      ></div>
    </button>

    <!-- Tooltip for Auto/Manual Mode -->
    <Tooltip
      targetElement={tooltipTarget}
      text={$autoMode ? "Autochecking Quests" : "Manual Quest Checking"}
      inlineMode={true}
      offsetX={5}
    ></Tooltip>
  </div>

  <!-- Share progress generate -->
  <button
    on:click={onShareProgressClicked}
    class="ml-4 p-2 rounded-lg shadow transition-colors duration-300 text-xs sm:text-base bg-white text-gray-700 border border-gray-300 hover:bg-gray-100"
  >
    🔗 Share
  </button>

  <!-- Last Quest Button -->
  <button
    on:click={onScrollToLastQuestClicked}
    class="ml-4 p-2 rounded-lg shadow transition-colors duration-300 text-xs sm:text-base
    {lastCheckedQuestId === null
      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100'}"
    disabled={lastCheckedQuestId === null}
    aria-disabled={lastCheckedQuestId === null}
  >
    <span class="block sm:hidden">Goto Quest</span>
    <span class="hidden sm:block">Scroll to Current Quest</span>
  </button>

  <!-- Scroll Top -->
  {#if $showScrollToTop}
    <button
      on:click={onScrollToTopClicked}
      class="ml-4 p-2 rounded-lg shadow transition-colors duration-300 text-xs sm:text-base bg-white text-gray-700 border border-gray-300 hover:bg-gray-100"
    >
      ↑
    </button>
  {/if}
</div>
