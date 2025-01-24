<script lang="ts">
  // Dependencies imports
  import { onMount, onDestroy, tick, SvelteComponent } from "svelte";
  import { fade } from "svelte/transition";
  import { get } from "svelte/store";
  import { debounce } from "lodash";

  // Application imports
  import "../app.css";
  import { base } from "$app/paths";

  // Lib imports
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
  import Modal from "$lib/components/Modal.svelte";

  // Stores imports
  import {
    quests,
    completedQuests,
    filteredQuests,
    isLoadingQuests,
    setQuestCompletion,
    setSingleQuestCompletion,
    currentExpansion,
    updateCurrentExpansion,
    getLastCheckedQuest,
  } from "$lib/stores/questsStore";
  import {
    initAllExpansionProgress,
    hasSharedProgress,
    generateShareableLink,
    loadSharedProgress,
    progress,
    groupProgress,
  } from "$lib/stores/progressStore";
  import {
    disableScrollToTop,
    enableScrollToTop,
  } from "$lib/stores/actionBarStore";
  import { openModal } from "$lib/stores/modalManager";

  // Exports
  export let data: { quests: ExpansionsQuests }; // Quest.csv data provided by load function

  // Properties
  let openExpansions: Record<string, boolean> = {};
  let openQuestGroups: Record<string, Record<string, boolean>> = {};
  let searchQuery = "";
  let autoMode = true;
  let showScrollToTop = false;
  let lastCheckedQuestNumber: number | null = null;
  let highlightedQuestNumber: number | null = null;
  let tooltipTarget: HTMLElement | null = null;
  let searchInput: SvelteComponent<Search>;

  function filterQuests(): void {
    const allQuests = get(quests);
    closeExpansionAndQuestGroups();

    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      filteredQuests.set(allQuests);
      return;
    }

    const filteredExpansions = allQuests.reduce<ExpansionsQuests>(
      (result, expansion) => {
        const filteredExpansion = filterExpansion(expansion, query);

        if (Object.keys(filteredExpansion.quests).length > 0) {
          result.push(filteredExpansion);
        }

        return result;
      },
      []
    );

    filteredQuests.set(filteredExpansions);
  }
  const debouncedFilterQuests = debounce(filterQuests, 250);

  function filterExpansion(expansion: Expansion, query: string): Expansion {
    const filteredExpansion: Expansion = {
      name: expansion.name,
      quests: {},
    };

    for (const questGroup in expansion.quests) {
      const matchingQuests = filterQuestGroupQuests(
        expansion.quests[questGroup],
        query
      );
      if (matchingQuests.length > 0) {
        filteredExpansion.quests[questGroup] = matchingQuests;
        openExpansions[expansion.name] = true;
        openQuestGroups[expansion.name][questGroup] = true;
      }
    }

    return filteredExpansion;
  }

  function filterQuestGroupQuests(
    questGroupQuests: Quest[],
    query: string
  ): Quest[] {
    return questGroupQuests.filter((quest) => {
      const nameMatches = quest.Name.toLowerCase().includes(query);
      const descriptionMatches = quest.Description
        ? quest.Description.toLowerCase().includes(query)
        : false;
      const unlockMatches = quest.Unlocks.some((unlock) =>
        unlock?.Name?.toLowerCase()?.includes(query)
      );

      return nameMatches || descriptionMatches || unlockMatches;
    });
  }

  function closeExpansionAndQuestGroups() {
    const $quests = get(quests);
    openExpansions = {};
    openQuestGroups = {};

    for (const expansion of $quests) {
      openExpansions[expansion.name] = false;
      openQuestGroups[expansion.name] = {};

      for (const questGroup of Object.keys(expansion.quests)) {
        openQuestGroups[expansion.name][questGroup] = false;
      }
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

  function scrollToTop() {
    const contentContainer =
      document.getElementsByClassName("content-container")[0];
    if (!contentContainer) return;
    contentContainer.scrollTo({ top: 0, behavior: "smooth" });
  }

  function scrollToLastCheckedQuest() {
    if (!lastCheckedQuestNumber) return;

    // Clear search if it exists
    if (searchQuery) {
      searchQuery = "";
      searchInput.clear();
      filterQuests();
    }

    // Wait for DOM updates before proceeding
    tick().then(() => {
      const questElement = document.getElementById(
        `quest-${lastCheckedQuestNumber}`
      );
      if (!questElement) return;

      // Open parent collapsibles
      openParentDetails(questElement);

      // Scroll to the quest and highlight it
      tick().then(() => {
        questElement.scrollIntoView({ behavior: "smooth", block: "center" });
        highlightQuest(questElement);
      });
    });
  }

  function openParentDetails(element: HTMLElement) {
    let parent = element.parentElement;
    while (parent) {
      if (
        parent.tagName === "DETAILS" &&
        parent instanceof HTMLDetailsElement
      ) {
        parent.open = true;
      }
      parent = parent.parentElement; // Traverse up the DOM
    }
  }

  function highlightQuest(element: HTMLElement) {
    highlightedQuestNumber = lastCheckedQuestNumber;
    setTimeout(() => {
      highlightedQuestNumber = null;
    }, 3000);
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

  function updateLastCheckedQuest() {
    const lastCheckedQuest = getLastCheckedQuest();
    lastCheckedQuestNumber = lastCheckedQuest ? lastCheckedQuest["#"] : null;
  }

  function updateQuest(quest: Quest, checked: boolean) {
    if (autoMode) {
      setQuestCompletion(quest, checked);
    } else {
      setSingleQuestCompletion(quest, checked);
    }

    updateLastCheckedQuest();
    updateBackground();
  }

  function simulateLoading() {
    setTimeout(() => {
      isLoadingQuests.set(false);

      if (isMobile()) {
        attachActionBar();
      }

      // The footer is not part of the Svelte app, so we need to manually append it
      if (!document.getElementById("footer")) {
        document?.body?.appendChild(
          new Footer({
            target: document.body,
          }).$$.root.firstChild
        );
      }
    }, 500);
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

    if (hasSharedProgress()) {
      openModal(
        "Shared Progress Warning",
        "You are viewing a shared progress link. Changing progress will alter yours, continue?",
        () => {
          updateQuest(quest, input.checked);
        },
        () => {
          // undo the checkbox change
          input.checked = !input.checked;
        },
        "Yes",
        "Cancel"
      );

      return;
    }

    updateQuest(quest, input.checked);
  }

  function handleSearchInput(event: CustomEvent) {
    searchQuery = event.detail; // Update the search query
    debouncedFilterQuests(); // Trigger the debounced filter
  }

  function initProgress() {
    if (hasSharedProgress()) {
      loadSharedProgress();
    }

    initAllExpansionProgress();
  }

  function initQuests(loadedQuests: ExpansionsQuests) {
    quests.set(loadedQuests);
    filteredQuests.set(loadedQuests);

    closeExpansionAndQuestGroups();
  }

  onMount(() => {
    const loadedQuests = data.quests;
    initQuests(loadedQuests);
    initProgress();

    updateLastCheckedQuest();
    updateCurrentExpansion();
    updateBackground();

    simulateLoading();

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
  <meta
    property="og:image:alt"
    content="Track and share your FFXIV MSQ progress easily!"
  />
  <!-- Preload backgrounds -->
  <link rel="prefetch" href="background_arealmreborn.webp" as="image" />
  <link rel="prefetch" href="background_heavensward.webp" as="image" />
  <link rel="prefetch" href="background_stormblood.webp" as="image" />
  <link rel="prefetch" href="background_shadowbringers.webp" as="image" />
  <link rel="prefetch" href="background_endwalker.webp" as="image" />
  <link rel="prefetch" href="background_dawntrail.webp" as="image" />
</svelte:head>

<Modal />

<Title />
{#if $isLoadingQuests}
  <Loading />
{:else}
  <ActionBar
    lastCheckedQuestId={lastCheckedQuestNumber}
    on:generateLink={generateShareableLink}
    on:scrollToLastQuest={scrollToLastCheckedQuest}
    on:scrollToTop={scrollToTop}
  />
  <Progress />
  <Search
    placeholder="Search quest name, description and unlocks..."
    bind:this={searchInput}
    bind:value={searchQuery}
    on:input={handleSearchInput}
  />
  {#each $filteredQuests as expansion}
    <details
      transition:fade
      class="relative mb-8 overflow-visible"
      open={openExpansions[expansion.name]}
    >
      <summary
        class="flex justify-between items-center text-xl sm:text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow transition-transform transform hover:scale-[1.02] hover:shadow-lg hover:z-[3] hover:relative"
      >
        {expansion.name}
        <!-- draw icon based on complete expansion progress or not -->
        {#if $progress[expansion.name].percent === 100}
          <img src="ffxiv_complete.webp" alt="Complete" class="w-6 h-6" />
        {:else}
          <img src="ffxiv_incomplete.webp" alt="Incomplete" class="w-6 h-6" />
        {/if}
      </summary>
      {#each Object.keys(expansion.quests) as questGroup}
        <details
          class="ml-6 mb-6 pl-6"
          open={openQuestGroups[expansion.name][questGroup]}
        >
          {#if questGroup !== "Main"}
            <summary
              class="flex justify-between items-center text-xl font-semibold text-gray-600 cursor-pointer mb-3 bg-white rounded-lg p-4 shadow transition-transform transform hover:scale-[1.01] hover:bg-gray-100 hover:shadow-md"
            >
              {questGroup}
              <div class="text-right">
                {$groupProgress[expansion.name][questGroup]
                  .completed}/{$groupProgress[expansion.name][questGroup].total}
              </div>
            </summary>
          {/if}
          <ul class="space-y-4">
            {#each expansion.quests[questGroup] as quest (quest["#"])}
              <li
                id={`quest-${quest["#"]}`}
                class="flex flex-col sm:flex-row items-center p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-300 hover:border-blue-300"
                class:border-2={highlightedQuestNumber === quest["#"]}
                class:border-blue-600={highlightedQuestNumber === quest["#"]}
                class:animate-flicker={highlightedQuestNumber === quest["#"]}
              >
                <div class="flex-none w-10 sm:w-16 mb-4 sm:mb-0">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-green-500 bg-gray-100 border-gray-300 rounded focus:ring-2 focus:ring-blue-300 focus:bg-blue-50 checked:bg-blue-100 transition-color"
                    bind:checked={$completedQuests[quest["#"]]}
                    on:change={(e) => handleCheckboxChange(e, quest)}
                  />
                </div>

                <div class="flex-grow sm:ml-4 text-center sm:text-left">
                  <div class="flex items-center">
                    <p class="font-bold text-lg sm:text-xl text-gray-800">
                      {quest.Name}
                      {#if isMobile()}
                        <a
                          href={getGarlandToolsQuestURLByID(quest["#"])}
                          target="_blank"
                          class="text-blue-500 underline hover:text-blue-600"
                        >
                          (View on Garland Tools)
                        </a>
                      {/if}
                    </p>
                    {#if quest["#"] === lastCheckedQuestNumber}
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

  <!-- No results container (fade hack) -->
  <div class="relative">
    {#if $filteredQuests && $filteredQuests.length === 0}
      <div transition:fade class="absolute inset-0">
        <div class="flex justify-center">
          <div class="inline-block p-4 bg-white rounded-lg shadow">
            <p class="text-center text-gray-600">No quests found.</p>
          </div>
        </div>
        <img
          src="moogle_no_results.png"
          alt="A moogle displaying no results found"
          loading="lazy"
          class="mx-auto mt-2 w-3/12 max-w-max min-w-20 object-contain"
        />
      </div>
    {/if}
  </div>
{/if}
