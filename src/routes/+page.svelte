<script lang="ts">
  // Dependencies imports
  import { onMount, onDestroy, tick } from "svelte";
  import { fade } from "svelte/transition";
  import { get } from "svelte/store";
  import { debounce } from "lodash";
  import {
    compressToEncodedURIComponent,
    decompressFromEncodedURIComponent,
  } from "lz-string";

  // Application imports
  import "../app.css";
  import { base } from "$app/paths";
  import type { QuestsState } from "./+page";

  // Lib imports
  import {
    quests,
    loading,
    filteredQuests,
    completedQuests,
    currentExpansion,
    toggleQuestCompletion,
    toggleSingleQuestCompletion,
    updateCurrentExpansion,
  } from "$lib/stores/questsStore";
  import { calculateAllProgress } from "$lib/stores/progressStore";
  import { getImageUrl } from "$lib/services/xivapi";
  import {
    getGarlandToolsQuestURLByID,
    sanitizeFFXIVMarkUp,
    createMagicParticles,
    isMobile,
  } from "$lib/utils";
  import type { Quest, ExpansionsQuests, Expansion } from "$lib/model";

  // Component imports
  import Title from "$lib/components/Title.svelte";
  import ActionBar from "$lib/components/ActionBar.svelte";
  import Progress from "$lib/components/Progress.svelte";
  import Footer from "$lib/components/Footer.svelte";
  import Loading from "$lib/components/Loading.svelte";
  import Search from "$lib/components/Search.svelte";
  import Tooltip from "$lib/components/Tooltip.svelte";
  import {
    disableScrollToTop,
    enableScrollToTop,
  } from "$lib/stores/actionBarStore";

  // Exports
  export let data: QuestsState;

  // Properties
  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let searchQuery = "";
  let autoMode = true;
  let showScrollToTop = false;
  let lastCheckedQuestId: number | null = null;
  let highlightedQuestId: number | null = null;
  let tooltipTarget: HTMLElement | null = null;
  let searchInput: HTMLInputElement;

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

  function handleScroll() {
    const contentContainer =
      document.getElementsByClassName("content-container")[0];
    if (!contentContainer) return;

    showScrollToTop = contentContainer.scrollTop > 140;

    if (showScrollToTop) {
      enableScrollToTop();

      if (isMobile()) return;
      detachActionBar();
    } else {
      disableScrollToTop();

      if (isMobile()) return;
      attachActionBar();
    }
  }

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

  function handleSearchInput(event: CustomEvent) {
    searchQuery = event.detail; // Update the search query
    debouncedFilterQuests(); // Trigger the debounced filter
  }

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

  onMount(() => {
    // Load shared progress if available
    loadSharedProgress();

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

        // Mobile check
        if (isMobile()) {
          attachActionBar();
        }

        // Append the footer after the page is loaded
        if (!document.getElementById("footer")) {
          document?.body?.appendChild(
            new Footer({
              target: document.body,
            }).$$.root.firstChild
          );
        }
      }, 750);
    });

    // Events
    document
      .getElementsByClassName("content-container")[0]
      .addEventListener("scroll", handleScroll);
  });

  onDestroy(() => {
    document
      .getElementsByClassName("content-container")[0]
      .removeEventListener("scroll", handleScroll);
  });

  // Reactively update the background whenever the current expansion changes
  $: updateBackground();
</script>

<svelte:head>
  <!-- OG Tags -->
  <title>FFXIV Journey</title>
  <meta property="og:type" content="website" />
  <meta property="og:image:alt" content="FFXIV MSQ Progress Tracker preview" />
  <!-- Preload backgrounds -->
  <link rel="prefetch" href="background_arealmreborn.webp" as="image" />
  <link rel="prefetch" href="background_heavensward.webp" as="image" />
  <link rel="prefetch" href="background_stormblood.webp" as="image" />
  <link rel="prefetch" href="background_shadowbringers.webp" as="image" />
  <link rel="prefetch" href="background_endwalker.webp" as="image" />
  <link rel="prefetch" href="background_dawntrail.webp" as="image" />
</svelte:head>

<Title />

{#if !$loading}
  <ActionBar
    {lastCheckedQuestId}
    on:generateLink={generateShareableLink}
    on:scrollToLastQuest={scrollToLastCheckedQuest}
    on:scrollToTop={scrollToTop}
  />

  <Progress />
{/if}

{#if $loading}
  <Loading />
{:else}
  <Search
    placeholder="Search quest name, description and unlocks..."
    bind:value={searchQuery}
    on:input={handleSearchInput}
  />

  {#each $filteredQuests as expansion}
    <details transition:fade class="mb-8" open={openExpansions[expansion.name]}>
      <summary
        class="text-xl sm:text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow"
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
                        bind:this={tooltipTarget}
                        src="moogle_current_quest.png"
                        alt="Current Quest"
                        class="ml-2 h-8 w-8"
                      />
                      <Tooltip
                        text="Current MSQ Quest!"
                        targetElement={tooltipTarget}
                        orientation="right"
                      />
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
                        src={getImageUrl(unlock.Image)}
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
    {#if $filteredQuests && $filteredQuests.length === 0}
      <div class="flex justify-center">
        <div class="inline-block p-4 bg-white rounded-lg shadow">
          <p class="text-center text-gray-600">No quests found.</p>
        </div>
      </div>
      <img
        transition:fade
        src="moogle_no_results.png"
        alt="A moogle displaying no results found"
        loading="lazy"
        class="mx-auto mt-2 w-3/12 max-w-max min-w-20 object-contain"
      />
    {/if}
  {/if}
{/if}
