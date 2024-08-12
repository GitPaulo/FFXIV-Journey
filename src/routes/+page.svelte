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
    updateCurrentExpansion,
  } from "$lib/stores/questsStore";
  import type { Quest, ExpansionsQuests, Quests } from "$lib/model";

  export let data: { quests: Promise<ExpansionsQuests>; loading: boolean };

  let searchQuery = "";
  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let showTitle = true;
  let tooltipVisible = false;
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

  // Update the background image based on the current expansion
  function updateBackground() {
    const bgImage = $currentExpansion
      ? `${base}/background_${$currentExpansion.replace(/\s/g, "").toLowerCase()}.webp`
      : ""; // No background is default

    const bgElement = document.getElementById("background");
    if (bgElement) {
      bgElement.style.backgroundImage = `url('${bgImage}')`;
    }
  }

  // Toggle the visibility of the title section
  function toggleTitleVisibility() {
    showTitle = !showTitle;
  }

  // Show and hide the tooltip for the title close button
  function showTooltip() {
    tooltipVisible = true;
  }

  function hideTooltip() {
    tooltipVisible = false;
  }

  // Handle checkbox changes and update quest completion state
  function handleCheckboxChange(event: Event, quest: Quest) {
    const input = event.target as HTMLInputElement;
    toggleQuestCompletion(quest, input.checked);
    updateBackground();
  }

  // Handle keyboard shortcut to focus on the search bar
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === "/") {
      event.preventDefault(); // Prevent the default '/' action
      searchInput?.focus();
    }
  };
  window.addEventListener("keydown", handleKeydown);

  // Initialize the quests data and state
  $: {
    data.quests.then((loadedQuests: ExpansionsQuests) => {
      quests.set(loadedQuests);
      filteredQuests.set(loadedQuests);

      resetOpenStates();
      calculateAllProgress();
      updateCurrentExpansion();
      updateBackground();
      setTimeout(() => loading.set(false), 350);
    });
  }

  // Reactively update the background whenever the current expansion changes
  $: updateBackground();
</script>

<!-- Title -->
{#if showTitle}
  <div
    class="relative flex flex-col mb-8 justify-center items-center"
    transition:slide
  >
    <div class="bg-white rounded-lg p-6 shadow max-w-xl w-full relative">
      <!-- Hide Button -->
      <button
        on:click={toggleTitleVisibility}
        on:mouseover={showTooltip}
        on:mouseleave={hideTooltip}
        class="absolute top-2 right-2 text-gray-200 hover:text-gray-700 p-3"
      >
        ✕
        {#if tooltipVisible}
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
    <!-- Search Focus Icon -->
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
            {#each expansion.quests[location] as quest}
              <li
                class="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200"
              >
                <div class="flex-none w-10 sm:w-16">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    checked={$completedQuests[quest["#"]] || false}
                    on:change={(e) => handleCheckboxChange(e, quest)}
                  />
                </div>

                <div class="flex-grow ml-4">
                  <p class="font-bold text-lg sm:text-xl text-gray-800">
                    {quest.Name}
                  </p>
                  <p class="text-sm text-gray-500 mt-1 hidden sm:block">
                    ID: {quest.Id}
                  </p>
                  <p class="text-sm text-gray-400 mt-1 hidden sm:block">
                    <i>"{quest.Description}"</i>
                  </p>
                  <img
                    src={getImageUrl(quest.Image)}
                    alt="Quest journal thumbnail"
                    loading="lazy"
                    class="mt-4 w-44 h-16 rounded-md border border-gray-300 shadow-sm hidden sm:block"
                  />
                </div>
                <div class="ml-auto flex items-center">
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
