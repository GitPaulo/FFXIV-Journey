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
    showProgress,
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
  let isFiltering = false;
  let lastBackgroundExpansion: string = "";

  // Loading states
  // Yes, i know this is a gimmick...
  let isQuestsInitialized = false;
  let isProgressInitialized = false;
  let isBackgroundInitialized = false;
  let isComponentsInitialized = false;

  // Breadcrumb tracking
  let currentVisibleExpansion = "";
  let currentVisibleQuestGroup = "";
  let showBreadcrumb = false;

  // Hover override for breadcrumbs
  let hoverOverrideExpansion = "";
  let hoverOverrideQuestGroup = "";
  let isHoveringQuest = false;

  // Computed breadcrumb values (hover takes precedence over scroll-based)
  $: displayExpansion = isHoveringQuest
    ? hoverOverrideExpansion
    : currentVisibleExpansion;
  $: displayQuestGroup = isHoveringQuest
    ? hoverOverrideQuestGroup
    : currentVisibleQuestGroup;

  // Breadcrumb visibility logic:
  // - Never show during search/filtering
  // - Show when we've scrolled past headers OR when hovering
  // - This prevents hover breadcrumbs when headers are still visible
  $: shouldShowBreadcrumb = !searchQuery && !isFiltering && showBreadcrumb;

  $: isFullyLoaded =
    isQuestsInitialized &&
    isProgressInitialized &&
    isBackgroundInitialized &&
    isComponentsInitialized;
  $: loadingMessage = (() => {
    if (!isQuestsInitialized) return "Loading quest data... <b>kupo!</b>";
    if (!isProgressInitialized) return "Initializing progress... <b>kupo!</b>";
    if (!isBackgroundInitialized)
      return "Setting up backgrounds... <b>kupo!</b>";
    if (!isComponentsInitialized) return "Preparing components... <b>kupo!</b>";
    return "Almost ready... <b>kupo!</b>";
  })();

  /**
   * Helper function to get the main content container element
   * @returns The content container element or null if not found
   */
  function getContentContainer(): HTMLElement | null {
    return (
      (document.getElementsByClassName(
        "content-container"
      )[0] as HTMLElement) || null
    );
  }

  function filterQuests(): void {
    isFiltering = true;
    const allQuests = get(quests);
    closeExpansionAndQuestGroups();

    const query = searchQuery.trim().toLowerCase();
    if (!query) {
      filteredQuests.set(allQuests);
      setTimeout(() => (isFiltering = false), 300); // Match fade transition duration
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
    setTimeout(() => (isFiltering = false), 300); // Match fade transition duration
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

  function handleExpansionToggle(expansionName: string, event: Event) {
    const details = event.target as HTMLDetailsElement;
    openExpansions[expansionName] = details.open;

    // If closing the expansion, also close all its quest groups
    if (!details.open) {
      for (const questGroup of Object.keys(
        openQuestGroups[expansionName] || {}
      )) {
        openQuestGroups[expansionName][questGroup] = false;
      }
    }
  }

  function handleQuestGroupToggle(
    expansionName: string,
    questGroup: string,
    event: Event
  ) {
    const details = event.target as HTMLDetailsElement;
    openQuestGroups[expansionName][questGroup] = details.open;
  }

  /**
   * Set the action bar position (fixed for detached, absolute for attached)
   * @param isDetached - Whether the action bar should be detached (fixed position)
   */
  function setActionBarPosition(isDetached: boolean) {
    const actionBar = document.getElementById("action-bar");
    if (actionBar) {
      actionBar.style.position = isDetached ? "fixed" : "absolute";
    }
  }

  function scrollToExpansion(expansionName: string) {
    if (!expansionName) return;

    // Clear search if it exists
    if (searchQuery) {
      searchQuery = "";
      searchInput.clear();
      filterQuests();
    }

    // Wait for DOM updates before proceeding
    tick().then(() => {
      const expansionId = `expansion-${expansionName.replace(/\s/g, "-").toLowerCase()}`;
      const expansionElement = document.getElementById(expansionId);
      if (!expansionElement) return;

      // Open the expansion details if it's closed
      if (
        expansionElement instanceof HTMLDetailsElement &&
        !expansionElement.open
      ) {
        expansionElement.open = true;
        openExpansions[expansionName] = true;
      }

      // Scroll to the expansion
      tick().then(() => {
        expansionElement.scrollIntoView({ behavior: "smooth", block: "start" });
      });
    });
  }

  function scrollToTop() {
    const contentContainer = getContentContainer();
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
    const bgElement = document.getElementById("background");
    if (!bgElement) return;

    const expansion = get(currentExpansion);
    const progressVisible = get(showProgress);

    // Determine target background
    const bgImage =
      progressVisible && expansion
        ? `url('${base}/background_${expansion.replace(/\s/g, "").toLowerCase()}.webp')`
        : "";

    // Fade transition
    bgElement.style.opacity = "0";
    setTimeout(() => {
      bgElement.style.backgroundImage = bgImage;
      bgElement.style.opacity = bgImage ? "0.9" : "0";
    }, 300);
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
    updateCurrentExpansion();
    updateBackground();
  }

  async function simulateLoading() {
    // Remove artificial delay - loading will complete when all tasks are done
    if (isMobile()) {
      setActionBarPosition(false); // Attach action bar for mobile
    }

    // Small delay to show component loading state
    await new Promise((resolve) => setTimeout(resolve, 200));
    isComponentsInitialized = true;
  }

  function completeLoading() {
    // Only hide loading when everything is actually ready
    if (isFullyLoaded) {
      isLoadingQuests.set(false);
    }
  }

  // Watch for loading completion
  $: if (isFullyLoaded) {
    completeLoading();
  }

  function handleScroll() {
    const contentContainer = getContentContainer();
    if (!contentContainer) return;

    showScrollToTop = contentContainer.scrollTop > 140;

    // Update breadcrumb with simple scroll detection
    updateBreadcrumb();

    if (showScrollToTop) {
      enableScrollToTop();

      if (isMobile()) return;
      setActionBarPosition(true); // Detach action bar
    } else {
      disableScrollToTop();

      if (isMobile()) return;
      setActionBarPosition(false); // Attach action bar
    }
  }

  function handleQuestHover(
    quest: Quest,
    expansionName: string,
    questGroupName: string
  ): void {
    isHoveringQuest = true;
    hoverOverrideExpansion = expansionName;

    // Format quest group name, removing expansion prefix
    const formattedQuestGroup = formatIdToTitle(
      `questgroup-${questGroupName.toLowerCase().replace(/\s/g, "-")}`,
      "questgroup"
    );
    hoverOverrideQuestGroup =
      formattedQuestGroup.toLowerCase() !== "main" ? formattedQuestGroup : "";
  }

  function handleQuestHoverEnd(): void {
    isHoveringQuest = false;
    hoverOverrideExpansion = "";
    hoverOverrideQuestGroup = "";
  }

  function formatIdToTitle(
    id: string,
    type: "expansion" | "questgroup"
  ): string {
    const cleaned = id
      .replace(`${type}-`, "")
      .replace(/-/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());

    // For quest groups, remove expansion name prefixes to keep breadcrumbs concise
    if (type === "questgroup") {
      const EXPANSION_PREFIXES = [
        "A Realm Reborn ",
        "Heavensward ",
        "Stormblood ",
        "Shadowbringers ",
        "Endwalker ",
        "Dawntrail ",
      ];

      for (const prefix of EXPANSION_PREFIXES) {
        if (cleaned.startsWith(prefix)) {
          return cleaned.replace(prefix, "");
        }
      }
    }

    return cleaned;
  }

  function isElementOutOfView(element: Element, threshold: number): boolean {
    return element.getBoundingClientRect().top < -threshold;
  }

  function findActiveQuestGroup(
    expansionElement: HTMLElement,
    threshold: number
  ): string {
    const questGroupHeaders = expansionElement.querySelectorAll(
      '[id^="questgroup-"] > summary'
    );

    let lastActiveQuestGroup = "";

    // Check all quest groups and keep track of the last one that's out of view
    for (const header of questGroupHeaders) {
      if (isElementOutOfView(header, threshold)) {
        const questGroupElement = header.closest(
          '[id^="questgroup-"]'
        ) as HTMLElement;
        const questGroupName = formatIdToTitle(
          questGroupElement.id,
          "questgroup"
        );

        // Skip "Main" quest groups as they don't provide useful breadcrumb context
        if (questGroupName.toLowerCase() !== "main") {
          lastActiveQuestGroup = questGroupName;
        }
      }
    }

    return lastActiveQuestGroup;
  }

  function updateBreadcrumb(): void {
    const contentContainer = getContentContainer();
    if (!contentContainer) return;

    const SCROLL_THRESHOLD = 100; // Distance above viewport to consider "out of view"

    let currentExpansion = "";
    let currentQuestGroup = "";
    let hasScrolledPastAnyHeader = false;

    // Find the most recent expansion header that has scrolled out of view
    const expansionHeaders = document.querySelectorAll(
      '[id^="expansion-"] > summary'
    );

    for (const header of expansionHeaders) {
      if (isElementOutOfView(header, SCROLL_THRESHOLD)) {
        hasScrolledPastAnyHeader = true;

        const expansionElement = header.closest(
          '[id^="expansion-"]'
        ) as HTMLElement;
        currentExpansion = formatIdToTitle(expansionElement.id, "expansion");

        // Find the active quest group within this expansion
        currentQuestGroup = findActiveQuestGroup(
          expansionElement,
          SCROLL_THRESHOLD
        );
      }
    }

    // Update component state with discovered breadcrumb context
    currentVisibleExpansion = currentExpansion;
    currentVisibleQuestGroup = currentQuestGroup;
    showBreadcrumb = hasScrolledPastAnyHeader && currentExpansion !== "";
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

  async function initProgress() {
    if (hasSharedProgress()) {
      await loadSharedProgress();
    }

    initAllExpansionProgress();

    await new Promise((resolve) => setTimeout(resolve, 250));
    isProgressInitialized = true;
  }

  async function initQuests(loadedQuests: ExpansionsQuests) {
    quests.set(loadedQuests);
    filteredQuests.set(loadedQuests);

    closeExpansionAndQuestGroups();

    await new Promise((resolve) => setTimeout(resolve, 200));
    isQuestsInitialized = true;
  }

  async function initBackground() {
    updateBackground();

    await new Promise((resolve) => setTimeout(resolve, 220));
    isBackgroundInitialized = true;
  }

  onMount(async () => {
    const loadedQuests = data.quests;

    // Initialize each component and mark completion with small delays
    await initQuests(loadedQuests);
    await initProgress();

    updateLastCheckedQuest();
    updateCurrentExpansion();
    await initBackground();

    await simulateLoading();

    // Events
    const contentContainer = getContentContainer();
    if (contentContainer) {
      contentContainer.addEventListener("scroll", handleScroll);
    }
  });

  onDestroy(() => {
    const contentContainer = getContentContainer();
    if (contentContainer) {
      contentContainer.removeEventListener("scroll", handleScroll);
    }
  });

  // Reactively update the background whenever the current expansion or showProgress changes
  $: $showProgress, $currentExpansion, updateBackground();
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
  <Loading message={loadingMessage} />
{:else}
  <ActionBar
    lastCheckedQuestId={lastCheckedQuestNumber}
    on:generateLink={generateShareableLink}
    on:scrollToLastQuest={scrollToLastCheckedQuest}
    on:scrollToTop={scrollToTop}
  />
  {#if $showProgress}
    <Progress />
  {/if}
  <Search
    placeholder="Search quest name, description and unlocks..."
    bind:this={searchInput}
    bind:value={searchQuery}
    on:input={handleSearchInput}
  />

  <!-- Floating Breadcrumb -->
  {#if shouldShowBreadcrumb}
    <div
      class="floating-breadcrumb sticky top-0 z-10 mx-4 mb-4 bg-white rounded-lg shadow-md border border-gray-300 px-4 py-3 transition-all duration-300"
      style="margin-top: -1rem;"
    >
      <div class="flex items-center text-sm text-gray-600 font-medium">
        <svg
          class="w-4 h-4 mr-2 text-gray-400"
          fill="currentColor"
          viewBox="0 0 20 20"
        >
          <path
            fill-rule="evenodd"
            d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z"
            clip-rule="evenodd"
          />
        </svg>
        <button
          on:click={() => scrollToExpansion(displayExpansion)}
          class="text-blue-600 font-semibold hover:text-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded transition-colors duration-200"
        >
          {displayExpansion}
        </button>
        {#if displayQuestGroup}
          <svg
            class="w-3 h-3 mx-2 text-gray-400"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clip-rule="evenodd"
            />
          </svg>
          <span class="text-gray-700">{displayQuestGroup}</span>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Expansion Details -->
  {#each $filteredQuests as expansion}
    <details
      id="expansion-{expansion.name.replace(/\s/g, '-').toLowerCase()}"
      transition:fade
      class="relative mb-8 overflow-visible"
      open={openExpansions[expansion.name]}
      on:toggle={(event) => handleExpansionToggle(expansion.name, event)}
    >
      <summary
        class="flex justify-between items-center text-xl sm:text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow transition-all duration-300 transform hover:scale-[1.02] hover:shadow-lg hover:z-[3] hover:relative focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
      >
        {expansion.name}
        {#if $showProgress}
          {#if $progress[expansion.name].percent === 100}
            <img
              src="ffxiv_complete.webp"
              alt="Complete"
              class="w-6 h-6"
              title="All quests completed"
            />
          {:else}
            <img
              src="ffxiv_incomplete.webp"
              alt="Incomplete"
              class="w-6 h-6"
              title="In progress"
            />
          {/if}
        {/if}
      </summary>
      {#each Object.keys(expansion.quests) as questGroup}
        <details
          id="questgroup-{expansion.name
            .replace(/\s/g, '-')
            .toLowerCase()}-{questGroup.replace(/\s/g, '-').toLowerCase()}"
          class="ml-6 mb-6 pl-6"
          open={openQuestGroups[expansion.name][questGroup]}
          on:toggle={(event) =>
            handleQuestGroupToggle(expansion.name, questGroup, event)}
        >
          {#if questGroup !== "Main"}
            <summary
              class="flex justify-between items-center text-xl font-semibold text-gray-600 cursor-pointer mb-3 bg-white rounded-lg p-4 shadow transition-all duration-300 transform hover:scale-[1.01] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
            >
              {questGroup}
              {#if $showProgress}
                <div class="text-right">
                  {$groupProgress[expansion.name][questGroup]
                    .completed}/{$groupProgress[expansion.name][questGroup]
                    .total}
                </div>
              {/if}
            </summary>
          {/if}
          <ul class="space-y-4">
            {#each expansion.quests[questGroup] as quest (quest["#"])}
              <li
                id={`quest-${quest["#"]}`}
                class="flex flex-col sm:flex-row items-center p-4 bg-white rounded-lg shadow-md hover:shadow-lg transition-shadow border border-gray-300 hover:border-blue-500"
                class:border-2={highlightedQuestNumber === quest["#"]}
                class:border-blue-600={highlightedQuestNumber === quest["#"]}
                class:animate-flicker={highlightedQuestNumber === quest["#"]}
                on:mouseenter={() =>
                  handleQuestHover(quest, expansion.name, questGroup)}
                on:mouseleave={handleQuestHoverEnd}
              >
                {#if $showProgress}
                  <div class="flex-none w-10 sm:w-16 mb-4 sm:mb-0">
                    <input
                      type="checkbox"
                      class="form-checkbox h-6 w-6 text-blue-500 bg-gray-100 border-gray-300 rounded-sm focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 focus:bg-blue-50 checked:bg-blue-100 transition-all duration-300"
                      bind:checked={$completedQuests[quest["#"]]}
                      on:change={(e) => handleCheckboxChange(e, quest)}
                    />
                  </div>
                {/if}

                <div class="flex-grow sm:ml-4 text-center sm:text-left">
                  <div class="flex items-center">
                    <p class="font-bold text-lg sm:text-xl text-gray-800">
                      {quest.Name}
                      {#if isMobile()}
                        <a
                          href={getGarlandToolsQuestURLByID(quest["#"])}
                          target="_blank"
                          class="text-blue-500 underline hover:text-blue-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 rounded transition-all duration-300"
                        >
                          (View on Garland Tools)
                        </a>
                      {/if}
                    </p>
                    {#if $showProgress && quest["#"] === lastCheckedQuestNumber}
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
                <div class="ml-auto hidden sm:flex sm:items-center">
                  <a
                    href={getGarlandToolsQuestURLByID(quest["#"])}
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-white text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap"
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
                        loading="lazy"
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

  <!-- No results container -->
  <div class="relative">
    {#if $filteredQuests && $filteredQuests.length === 0}
      <div
        transition:fade
        class="absolute inset-0"
        style="opacity: {isFiltering ? 0 : 1}; pointer-events: {isFiltering
          ? 'none'
          : 'auto'}"
      >
        <div class="flex justify-center">
          <div class="inline-block p-4 bg-white rounded-lg shadow">
            <p class="text-center text-gray-600">No quests found.</p>
            <img
              src="moogle_no_results.png"
              alt="A moogle displaying no results found"
              loading="lazy"
              class="mx-auto mt-2 w-3/12 max-w-max min-w-20 object-contain"
            />
          </div>
        </div>
      </div>
    {/if}
  </div>
{/if}

<Footer />
