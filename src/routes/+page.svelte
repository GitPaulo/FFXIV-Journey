<script lang="ts">
  import { get } from "svelte/store";
  import { onMount, onDestroy, tick } from "svelte";

  import { debounce } from "lodash";
  import {
    compressToEncodedURIComponent,
    decompressFromEncodedURIComponent,
  } from "lz-string";

  import "../app.css";
  import { base } from "$app/paths";
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
  import { showTitle } from "$lib/stores/titleStore";
  import Title from "$lib/components/Title.svelte";
  import ActionBar from "$lib/components/ActionBar.svelte";
  import Progress from "$lib/components/Progress.svelte";
  import Footer from "$lib/components/Footer.svelte";
  import { getImageUrl, getOldImageUrl } from "$lib/services/xivapi";
  import {
    getGarlandToolsQuestURLByID,
    sanitizeFFXIVMarkUp,
    createMagicParticles,
  } from "$lib/utils";

  import type { QuestsState } from "./+page";
  import type { Quest, ExpansionsQuests, Expansion } from "$lib/model";

  export let data: QuestsState;

  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let autoMode = true;
  let showCurrentTooltip = false;
  let searchInput: HTMLInputElement;
  let searchQuery = "";
  let lastCheckedQuestId: number | null = null;
  let highlightedQuestId: number | null = null;

  function enableCurrentTooltip() {
    showCurrentTooltip = true;
  }

  function disableCurrentTooltip() {
    showCurrentTooltip = false;
  }

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
  function filterQuests(): void {
    const $quests = get(quests);
    resetOpenStates();

    const trimmedQuery = searchQuery.trim().toLowerCase();
    if (!trimmedQuery) {
      filteredQuests.set($quests);
      return;
    }

    const filteredExpansions: ExpansionsQuests =
      $quests.reduce<ExpansionsQuests>((acc, expansion) => {
        const filteredExpansion: Expansion = {
          name: expansion.name,
          quests: {},
        };

        for (const location in expansion.quests) {
          const locationQuests = expansion.quests[location].filter((quest) => {
            const nameMatches = quest.Name.toLowerCase().includes(trimmedQuery);
            const descriptionMatches = quest.Description
              ? quest.Description.toLowerCase().includes(trimmedQuery)
              : false;
            const unlockMatches = quest.Unlocks.some((unlock) =>
              unlock?.Name?.toLowerCase()?.includes(trimmedQuery)
            );

            return nameMatches || descriptionMatches || unlockMatches;
          });

          if (locationQuests.length > 0) {
            filteredExpansion.quests[location] = locationQuests;
            openExpansions[expansion.name] = true;
            openLocations[expansion.name][location] = true;
          }
        }

        if (Object.keys(filteredExpansion.quests).length > 0) {
          acc.push(filteredExpansion);
        }

        return acc;
      }, []);

    filteredQuests.set(filteredExpansions);
  }
  const debouncedFilterQuests = debounce(filterQuests, 250);

  // Find the last checked quest based on the order of expansions in the quests store
  function findLastCheckedQuest(): void {
    const $completedQuests = get(completedQuests);
    const $quests = get(quests);

    let lastCheckedQuest = null;

    // Iterate through each expansion in the order it appears in $quests
    for (const expansion of $quests) {
      for (const location in expansion.quests) {
        const questsInLocation = expansion.quests[location];

        for (const quest of questsInLocation) {
          if ($completedQuests[quest["#"]]) {
            lastCheckedQuest = quest;
          }
        }
      }
    }

    // Update the last checked quest ID
    lastCheckedQuestId = lastCheckedQuest ? lastCheckedQuest["#"] : null;
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

  function detachActionBar() {
    const actionBar = document.getElementById("action-bar");
    if (actionBar) {
      actionBar.style.position = "fixed";
    }
  }

  function attachActionBar() {
    const actionBar = document.getElementById("action-bar");
    if (actionBar) {
      actionBar.style.position = "absolute";
    }
  }

  function isQuestCompleted(completedQuest: any): boolean {
    return Boolean(completedQuest);
  }

  function scrollToTop() {
    const contentContainer =
      document.getElementsByClassName("content-container")[0];
    if (!contentContainer) return;
    contentContainer.scrollTo({ top: 0, behavior: "smooth" });
  }

  function scrollToLastCheckedQuest() {
    if (lastCheckedQuestId === null) return;
    if (searchQuery) {
      searchQuery = "";
      searchInput.value = "";
      filterQuests(); // Clear the search
    }

    // Wait for the DOM to update after clearing the search
    tick().then(() => {
      const questElement = document.getElementById(
        `quest-${lastCheckedQuestId}`
      );

      if (questElement) {
        // Open all parent collapsibles (details elements)
        let parentElement = questElement.parentElement as HTMLElement | null;
        while (parentElement) {
          if (
            parentElement.tagName === "DETAILS" &&
            parentElement instanceof HTMLDetailsElement
          ) {
            parentElement.open = true;
          }
          parentElement = parentElement.parentElement; // Traverse up the DOM
        }

        // Wait for the collapsibles to be fully opened
        tick().then(() => {
          questElement.scrollIntoView({ behavior: "smooth", block: "center" });

          // Highlight the quest for 3 seconds
          highlightedQuestId = lastCheckedQuestId;
          setTimeout(() => {
            highlightedQuestId = null;
          }, 3000);
        });
      }
    });
  }

  // Generate a compact shareable link
  function generateShareableLink() {
    const completed = get(completedQuests);
    const completedIds = Object.keys(completed).filter(
      (id) => completed[Number(id)]
    );

    const state = {
      completedQuests: completedIds, // Store completed quest IDs only
      currentExpansion: get(currentExpansion), // Store current expansion
    };

    const compressedState = compressToEncodedURIComponent(
      JSON.stringify(state)
    );
    const basePath =
      window.location.origin + window.location.pathname.replace(/\/$/, ""); // Remove trailing slash
    const shareableLink = `${basePath}?progress=${compressedState}`;

    navigator.clipboard
      .writeText(shareableLink)
      .then(() =>
        alert("Progress link copied to clipboard! Share it with your friends!")
      )
      .catch(() => alert("Failed to copy link. Please try again."));
  }

  let showScrollToTop = false;
  function handleScroll() {
    const contentContainer =
      document.getElementsByClassName("content-container")[0];
    if (!contentContainer) return;

    showScrollToTop = contentContainer.scrollTop > 140;

    if (!showTitle) return;
    if (showScrollToTop) {
      detachActionBar();
    } else {
      attachActionBar();
    }
  }

  // Handle checkbox changes and update quest completion state
  function handleCheckboxChange(event: Event, quest: Quest) {
    const input = event.target as HTMLInputElement;
    createMagicParticles(input);

    if (autoMode) {
      toggleQuestCompletion(quest, input.checked);
    } else {
      toggleSingleQuestCompletion(quest, input.checked);
    }

    findLastCheckedQuest();
    updateBackground();
  }

  // Handle keyboard shortcut to focus on the search bar
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "/") {
      event.preventDefault(); // Prevent the default '/' action
      searchInput?.focus();
    }
  }

  // Load shared progress from a compact link
  function loadSharedProgress() {
    const urlParams = new URLSearchParams(window.location.search);
    const compressedState = urlParams.get("progress");

    if (compressedState) {
      try {
        const state = JSON.parse(
          decompressFromEncodedURIComponent(compressedState) || "{}"
        );

        // Reconstruct the state
        const completed: Record<number, boolean> = {};
        state.completedQuests.forEach((id: string) => {
          completed[Number(id)] = true;
        });

        completedQuests.set(completed);
        currentExpansion.set(state.currentExpansion);
      } catch (error) {
        console.error("Failed to decode shared progress:", error);
      }
    }
  }

  let metaTitle = "FFXIV Journey Tracker";
  let metaDescription =
    "Track and share your Main Story Quest progress in FFXIV with ease!";
  let metaImage = "/logo.png";
  function setupDynamicMetaTags() {
    const completed = Object.keys(get(completedQuests)).length;
    const expansion = get(currentExpansion) || "All Expansions";
    metaDescription = `Completed ${completed} quests in ${expansion}! Share your progress with friends!`;
  }

  onMount(() => {
    // Load shared progress if available
    loadSharedProgress();

    // setup meta tags
    setupDynamicMetaTags();

    data.quests.then((loadedQuests: ExpansionsQuests) => {
      // Init quests
      quests.set(loadedQuests);
      filteredQuests.set(loadedQuests);

      // Init state
      resetOpenStates();
      calculateAllProgress();
      updateCurrentExpansion();
      updateBackground();
      findLastCheckedQuest();

      // TODO: This is a hack, find a better way.
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
    document
      .getElementsByClassName("content-container")[0]
      .addEventListener("scroll", handleScroll);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
    document
      .getElementsByClassName("content-container")[0]
      .removeEventListener("scroll", handleScroll);
  });

  // Reactively update the background whenever the current expansion changes
  $: updateBackground();
</script>

<!-- Dynamic head -->
<svelte:head>
  <title>{metaTitle}</title>
  <meta property="og:title" content={metaTitle} />
  <meta property="og:description" content={metaDescription} />
  <meta property="og:image" content={metaImage} />
  <meta property="og:type" content="website" />
  <meta property="og:image:alt" content="FFXIV MSQ Progress Tracker preview" />
</svelte:head>

<!-- Title -->
{#if showTitle}
  <Title />
{/if}

{#if !$loading}
  <!-- Action Bar -->
  <ActionBar
    {lastCheckedQuestId}
    on:generateLink={generateShareableLink}
    on:scrollToLastQuest={scrollToLastCheckedQuest}
    on:scrollToTop={scrollToTop}
  />

  <!--- Progress --->
  <Progress {quests} {progress} />
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
      placeholder="Search quest name, description and unlocks..."
      autofocus
      class="p-3 pl-10 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
      bind:value={searchQuery}
      bind:this={searchInput}
      on:input={debouncedFilterQuests}
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
                id={`quest-${quest["#"]}`}
                class="flex flex-col sm:flex-row items-center p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-300 hover:border-blue-300"
                class:border-2={highlightedQuestId === quest["#"]}
                class:border-blue-600={highlightedQuestId === quest["#"]}
                class:animate-flicker={highlightedQuestId === quest["#"]}
              >
                <div class="flex-none w-10 sm:w-16 mb-4 sm:mb-0">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-green-500 bg-gray-100 border-gray-300 rounded focus:ring-2 focus:ring-blue-300 focus:bg-blue-50 checked:bg-blue-100 transition-color"
                    checked={isQuestCompleted($completedQuests[quest["#"]])}
                    on:change={(e) => handleCheckboxChange(e, quest)}
                  />
                </div>

                <div class="flex-grow sm:ml-4 text-center sm:text-left">
                  <div class="flex items-center">
                    <p class="font-bold text-lg sm:text-xl text-gray-800">
                      {quest.Name}
                    </p>
                    {#if quest["#"] === lastCheckedQuestId}
                      <img
                        src="moogle_current_quest.png"
                        alt="Current Quest"
                        class="ml-2 h-8 w-8"
                        on:mouseover={enableCurrentTooltip}
                        on:mouseleave={disableCurrentTooltip}
                        on:focus={enableCurrentTooltip}
                        on:blur={disableCurrentTooltip}
                      />
                      <!-- Tooltip for Current Quest Icon -->
                      {#if showCurrentTooltip}
                        <div
                          class="ml-2 bg-gray-800 text-white text-xs rounded py-1 px-2 shadow-lg"
                        >
                          Current MSQ Quest!
                        </div>
                      {/if}
                    {/if}
                  </div>
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
                    href={getGarlandToolsQuestURLByID(quest["#"])}
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-gray-200 text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-300 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-400 whitespace-nowrap"
                  >
                    <svg
                      class="mr-1"
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
