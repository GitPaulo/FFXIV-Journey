<script lang="ts">
  import "../app.css";
  import { base } from "$app/paths";
  import { get } from "svelte/store";
  import { slide } from "svelte/transition";
  import {
    quests,
    loading,
    progress,
    filteredQuests,
    completedQuests,
    currentExpansion,
    calculateAllProgress,
    toggleQuestCompletion,
    toggleSingleQuestCompletion,
    updateCurrentExpansion,
  } from "$lib/stores/questsStore";
  import Footer from "$lib/components/Footer.svelte";
  import type { Quest, ExpansionsQuests, Quests } from "$lib/model";
  import { onMount, onDestroy } from "svelte";

  export let data: { quests: Promise<ExpansionsQuests>; loading: boolean };

  let searchQuery = "";
  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let autoMode = true;
  let showTitle = true;
  let hideTooltipVisible = false;
  let toggleTooltipVisible = false;
  let searchInput: HTMLInputElement;

  // Reset the state of expansions and locations to be closed initially
  function resetOpenStates() {
    const $quests = get(quests);
    openExpansions = {};
    openLocations = {};

    for (const expansion of $quests) {
      openExpansions[expansion.name] = false;
      openLocations[expansion.name] = {};

      for (const location of Object.keys(expansion.quests)) {
        openLocations[expansion.name][location] = false;
      }
    }
  }

  // Filter quests based on search query
  function filterQuests() {
    const $quests = get(quests);
    resetOpenStates();

    if (!searchQuery.trim()) {
      filteredQuests.set($quests);
      return;
    }

    const result: ExpansionsQuests = $quests.reduce((acc, expansion) => {
      const filteredExpansion = {
        name: expansion.name,
        quests: {} as Quests,
      };

      for (const location in expansion.quests) {
        const locationQuests = expansion.quests[location].filter((quest) =>
          quest.Name.toLowerCase().includes(searchQuery.toLowerCase())
        );

        if (locationQuests.length) {
          filteredExpansion.quests[location] = locationQuests;
          openExpansions[expansion.name] = true;
          openLocations[expansion.name][location] = true;
        }
      }

      if (Object.keys(filteredExpansion.quests).length) {
        acc.push(filteredExpansion);
      }
      return acc;
    }, [] as ExpansionsQuests);

    filteredQuests.set(result);
  }

  // Get the correct image URL or fallback to placeholder
  function getImageUrl(imagePath: string | null): string {
    const placeholderImage = `${base}/default_quest_image.png`;
    if (
      !imagePath ||
      imagePath.trim() === "" ||
      imagePath.includes("000000_hr1") // Returned by XIVAPI for missing images
    ) {
      return placeholderImage;
    }
    try {
      const assetPath = `https://beta.xivapi.com/api/1/asset/${imagePath}?format=png`;
      new URL(assetPath);
      return assetPath;
    } catch {
      return placeholderImage;
    }
  }

  // TODO: Remove
  function getOldImageUrl(imagePath: string | null): string {
    if (!imagePath) {
      return "https://fakeimg.pl/300x160/2e2e2e/ab4444?text=Unknown"; // Placeholder unknown
    }
    return `https://xivapi.com/${imagePath}`;
  }

  // Update the background image based on the current expansion
  function updateBackground() {
    const bgImage = get(currentExpansion)
      ? `${base}/background_${get(currentExpansion).replace(/\s/g, "").toLowerCase()}.webp`
      : ""; // No background is default

    const bgElement = document.getElementById("background");
    if (bgElement) {
      bgElement.style.backgroundImage = `url('${bgImage}')`;
    }
  }

  // Toggle the visibility of the title section
  function toggleTitleVisibility() {
    showTitle = !showTitle;

    if (!showTitle) {
      const actionBar = document.getElementById("action-bar");
      if (actionBar) {
        actionBar.style.position = "fixed";
      }
    }
  }

  // Handle checkbox auto mode toggle
  function toggleAutoMode() {
    autoMode = !autoMode; // Toggle the autoMode flag
  }

  // Show and hide the tooltips
  function showTooltip() {
    toggleTooltipVisible = true;
  }

  function hideTooltip() {
    toggleTooltipVisible = false;
  }

  // Sanitize FFXIV markup for quest descriptions
  function sanitizeFFXIVMarkUp(description: string | null): string {
    return description
      ? description.replace(/<[^>]*>/g, "")
      : "This quest has no description.";
  }

  // Handle checkbox changes and update quest completion state
  function handleCheckboxChange(event: Event, quest: Quest) {
    const input = event.target as HTMLInputElement;

    if (autoMode) {
      // Auto mode: existing logic that may check/uncheck multiple quests
      toggleQuestCompletion(quest, input.checked);
    } else {
      // Manual mode: only toggle the state of the clicked checkbox
      toggleSingleQuestCompletion(quest, input.checked);
    }

    updateBackground();
  }

  // Handle keyboard shortcut to focus on the search bar
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "/") {
      event.preventDefault(); // Prevent the default '/' action
      searchInput?.focus();
    }
  }

  onMount(() => {
    // Initialize the quests data and state
    data.quests.then((loadedQuests: ExpansionsQuests) => {
      quests.set(loadedQuests);
      filteredQuests.set(loadedQuests);

      // Init state
      resetOpenStates();
      calculateAllProgress();
      updateCurrentExpansion();
      updateBackground();

      setTimeout(() => {
        loading.set(false);
        // Append the footer after the page is loaded
        document?.body?.appendChild(
          new Footer({
            target: document.body,
          }).$$.root.firstChild
        );
      }, 750);
    });

    // Events
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });

  // Reactively update the background whenever the current expansion changes
  $: updateBackground();
</script>

<!-- Title -->
{#if showTitle}
  <div
    class="relative flex flex-col mb-8 justify-center items-center"
    transition:slide
  >
    <div class="bg-white rounded-lg p-2 shadow max-w-xl w-full relative">
      <!-- Hide Button -->
      <button
        on:click={toggleTitleVisibility}
        on:mouseover={showTooltip}
        on:mouseleave={hideTooltip}
        class="absolute top-2 right-2 p-3 group"
      >
        <svg
          fill="currentColor"
          height="14px"
          width="14px"
          viewBox="0 0 330 330"
          xml:space="preserve"
          class="text-gray-300 group-hover:text-blue-500 transition-colors duration-200"
        >
          <path
            d="M325.607,304.394l-63.479-63.479c38.57-29.035,63.522-64.92,65.247-67.437c3.501-5.11,3.501-11.846,0-16.956
      c-2.925-4.269-72.659-104.544-162.371-104.544c-25.872,0-50.075,8.345-71.499,20.313L25.607,4.394
      c-5.857-5.858-15.355-5.858-21.213,0c-5.858,5.858-5.858,15.355,0,21.213l63.478,63.478C29.299,118.12,4.35,154.006,2.625,156.523
      c-3.5,5.109-3.5,11.845,0,16.955c2.925,4.268,72.65,104.546,162.378,104.546c25.868,0,50.069-8.345,71.493-20.314l67.897,67.898
      C307.323,328.536,311.161,330,315,330c3.839,0,7.678-1.464,10.606-4.394C331.465,319.749,331.465,310.252,325.607,304.394z
      M165.003,81.977c60.26,0,113.408,60.338,131.257,83.022c-9.673,12.294-29.705,35.629-55.609,54.439L115.673,94.461
      C131.079,86.902,147.736,81.977,165.003,81.977z M165.003,248.023c-60.285,0-113.439-60.364-131.273-83.037
      c9.651-12.303,29.652-35.658,55.574-54.47l124.99,124.99C198.884,243.084,182.236,248.023,165.003,248.023z"
          />
        </svg>
        {#if toggleTooltipVisible}
          <!-- Tooltip for Hide Button -->
          <div
            class="absolute top-full mt-1 right-0 bg-gray-800 text-white text-xs rounded py-1 px-2 shadow-lg"
          >
            Hide!
          </div>
        {/if}
      </button>

      <div class="text-center">
        <img src="logo.png" alt="FFXIV Journey" class="h-16 mx-auto" />
        <h1 class="text-3xl font-bold text-blue-600 mt-2">
          FFXIV Journey Tracker
        </h1>
      </div>

      <h3 class="font-bold text-center text-gray-600 mt-4 text-lg">
        Track your main story quest journey with the utmost ease.
      </h3>
    </div>
  </div>
{/if}

<!-- Action Bar -->
<div
  id="action-bar"
  class="fixed md:absolute top-2 mt-2 bg-white rounded-lg p-2 shadow"
>
  <!-- Toggle Button -->
  <div class="flex items-center">
    <button
      on:click={toggleAutoMode}
      on:mouseover={() => (hideTooltipVisible = true)}
      on:mouseleave={() => (hideTooltipVisible = false)}
      class={`w-12 h-6 flex items-center rounded-full p-1 transition-colors duration-300 ${
        autoMode ? "bg-gray-300" : "bg-blue-500"
      }`}
    >
      <div
        class={`h-4 w-4 rounded-full bg-white shadow-md transform transition-transform duration-300 ${
          autoMode ? "translate-x-0" : "translate-x-6"
        }`}
      ></div>
    </button>

    <!-- Tooltip for Auto/Manual Mode -->
    {#if hideTooltipVisible}
      <div
        class="ml-2 bg-gray-800 text-white text-xs rounded py-1 px-2 shadow-lg"
      >
        {autoMode ? "Autochecking Quests" : "Manual Quest Checking"}
      </div>
    {/if}
  </div>
</div>

<!--- Progress --->
{#if !$loading}
  <div
    class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg p-4 shadow"
  >
    {#each $quests as expansion}
      <div class="flex flex-col items-center">
        <p class="font-semibold text-gray-700">{expansion.name}</p>
        <div
          class="w-full bg-gray-200 rounded-full h-4 relative overflow-hidden shadow-inner"
        >
          <div
            class="h-full rounded-full bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 transition-all duration-700 ease-in-out"
            style="width: {$progress[expansion.name]?.percent}%"
          ></div>
          <p
            class="absolute w-full text-center text-xs font-semibold top-0 left-0 text-white"
          >
            {$progress[expansion.name]?.completed}/{$progress[expansion.name]
              ?.total} ({$progress[expansion.name]?.percent}%)
          </p>
        </div>
      </div>
    {/each}
  </div>
{/if}

<!-- Content -->
{#if $loading}
  <div class="bg-white p-4 rounded-lg shadow-md max-w-max mx-auto">
    <p class="text-center text-gray-600">
      Preparing your quests... <b>K-kupo!</b>
    </p>
  </div>
  <img src="loading.gif" alt="Loading" class="mx-auto mt-4" />
{:else}
  <div class="mb-6 flex relative">
    <input
      type="text"
      placeholder="Search quests..."
      autofocus
      class="p-3 pl-10 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
      bind:value={searchQuery}
      bind:this={searchInput}
      on:input={filterQuests}
    />
    <svg
      class="absolute top-1/2 left-3 transform -translate-y-1/2 text-gray-300 pointer-events-none"
      width="24px"
      height="24px"
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M13.2939 7.17041L11.9998 12L10.7058 16.8297"
        stroke="#888888"
        stroke-width="1.5"
        stroke-linecap="round"
      />
      <path
        d="M22 12C22 16.714 22 19.0711 20.5355 20.5355C19.0711 22 16.714 22 12 22C7.28595 22 4.92893 22 3.46447 20.5355C2 19.0711 2 16.714 2 12C2 7.28595 2 4.92893 3.46447 3.46447C4.92893 2 7.28595 2 12 2C16.714 2 19.0711 2 20.5355 3.46447C21.5093 4.43821 21.8356 5.80655 21.9449 8"
        stroke="#888888"
        stroke-width="1.5"
        stroke-linecap="round"
      />
    </svg>
  </div>

  {#each $filteredQuests as expansion}
    <details class="mb-8" open={openExpansions[expansion.name]}>
      <summary
        class="text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow"
      >
        {expansion.name}
      </summary>
      {#each Object.keys(expansion.quests) as location}
        <details
          class="ml-6 mb-6 pl-6"
          open={openLocations[expansion.name][location]}
        >
          {#if location !== "Main"}
            <summary
              class="text-xl font-semibold text-gray-600 cursor-pointer mb-3 bg-white rounded-lg p-4 shadow"
            >
              {location}
            </summary>
          {/if}
          <ul class="space-y-4">
            {#each expansion.quests[location] as quest (quest.Id)}
              <li
                class="flex flex-col sm:flex-row items-center p-4 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200"
              >
                <div class="flex-none w-10 sm:w-16 mb-4 sm:mb-0">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    checked={$completedQuests[quest["#"]] || false}
                    on:change={(e) => handleCheckboxChange(e, quest)}
                  />
                </div>

                <div class="flex-grow sm:ml-4 text-center sm:text-left">
                  <p class="font-bold text-lg sm:text-xl text-gray-800">
                    {quest.Name}
                  </p>
                  <p class="text-sm text-gray-500 mt-1 hidden sm:block">
                    ID: {quest.Id}
                  </p>
                  <p class="text-sm text-gray-400 mt-1 hidden sm:block">
                    <i>"{sanitizeFFXIVMarkUp(quest.Description)}"</i>
                  </p>
                  <img
                    src={getImageUrl(quest.Image)}
                    alt="Quest journal thumbnail"
                    loading="lazy"
                    class="mt-4 w-44 h-16 rounded-md border border-gray-300 shadow-sm hidden sm:block"
                  />
                </div>
                <div class="ml-auto flex items-center hidden sm:block">
                  <a
                    href={`https://www.garlandtools.org/db/#quest/${quest["#"]}`}
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-300 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 whitespace-nowrap"
                  >
                    <svg
                      class="mr-1"
                      xmlns="http://www.w3.org/2000/svg"
                      width="24px"
                      height="24px"
                      viewBox="0 0 24 24"
                      fill="none"
                    >
                      <path
                        d="M5 12V6C5 5.44772 5.44772 5 6 5H18C18.5523 5 19 5.44772 19 6V18C19 18.5523 18.5523 19 18 19H12M8.11111 12H12M12 12V15.8889M12 12L5 19"
                        stroke="#464455"
                        stroke-linecap="round"
                        stroke-linejoin="round"
                      />
                    </svg>

                    <span class="hidden sm:inline">Open in Garland Tools</span>
                  </a>
                </div>
              </li>
              {#if quest.Unlocks && quest.Unlocks.length > 0}
                <div
                  class="mt-4 ml-10 flex flex-col sm:flex-row sm:flex-wrap sm:justify-start gap-4"
                >
                  {#each quest.Unlocks as unlock}
                    <div
                      class="flex flex-col items-center p-4 bg-white rounded-lg shadow border border-gray-200"
                    >
                      <img
                        src={getOldImageUrl(unlock.Image)}
                        alt="{unlock.Name} thumbnail"
                        class="w-44 h-16 rounded-md border border-gray-300 shadow-sm mb-4 hidden sm:block"
                      />
                      <p class="font-bold text-gray-800 text-center">
                        {unlock.Name}
                      </p>
                      <p class="text-xs text-gray-500 text-center">
                        {unlock.ContentTypeName}
                      </p>
                    </div>
                  {/each}
                </div>
              {/if}
            {/each}
          </ul>
        </details>
      {/each}
    </details>
  {/each}

  {#if $filteredQuests && $filteredQuests.length === 0}
    <p class="text-center text-gray-600">No quests found.</p>
  {/if}
{/if}
