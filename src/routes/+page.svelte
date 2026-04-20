<script lang="ts">
  // Dependencies imports
  import { onMount, onDestroy, tick } from "svelte";
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
    FADE_IN,
    FADE_OUT,
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
    autoMode,
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
  let showScrollToTop = false;
  let lastCheckedQuestNumber: number | null = null;
  let highlightedQuestNumber: number | null = null;
  let tooltipTarget: HTMLElement | null = null;
  let expansionStatusRefs: Record<string, HTMLElement> = {};

  let searchInput: Search;
  let isFiltering = false;
  let isMobileDevice = false;
  let breadcrumbRafId: number | null = null;
  let loadingMessage = "Loading quest data... <b>kupo!</b>";

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
  // - Never show on mobile devices
  // - Never show during search/filtering
  // - Show when we've scrolled past headers OR when hovering
  // - This prevents hover breadcrumbs when headers are still visible
  $: shouldShowBreadcrumb =
    !isMobileDevice && !searchQuery && !isFiltering && showBreadcrumb;

  /**
   * Helper function to get the main content container element
   * @returns The content container element or null if not found
   */
  function getContentContainer(): HTMLElement | null {
    return (
      (document.getElementsByClassName(
        "content-container",
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
      [],
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
        query,
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
    query: string,
  ): Quest[] {
    return questGroupQuests.filter((quest) => {
      const nameMatches = quest.Name.toLowerCase().includes(query);
      const descriptionMatches = quest.Description
        ? quest.Description.toLowerCase().includes(query)
        : false;
      const unlockMatches = quest.Unlocks.some((unlock) =>
        unlock?.Name?.toLowerCase()?.includes(query),
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
        openQuestGroups[expansionName] || {},
      )) {
        openQuestGroups[expansionName][questGroup] = false;
      }
    }
  }

  function handleQuestGroupToggle(
    expansionName: string,
    questGroup: string,
    event: Event,
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
        `quest-${lastCheckedQuestNumber}`,
      );
      if (!questElement) return;

      // Open parent collapsibles
      openParentDetails(questElement);

      // Scroll to the quest and highlight it
      tick().then(() => {
        questElement.scrollIntoView({ behavior: "smooth", block: "center" });
        highlightQuest();
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

  function highlightQuest() {
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
    if ($autoMode) {
      setQuestCompletion(quest, checked);
    } else {
      setSingleQuestCompletion(quest, checked);
    }

    updateLastCheckedQuest();
    updateCurrentExpansion();
    updateBackground();
  }

  function completeLoading() {
    isLoadingQuests.set(false);
  }

  function handleScroll() {
    const contentContainer = getContentContainer();
    if (!contentContainer) return;

    showScrollToTop = contentContainer.scrollTop > 140;

    // Throttle breadcrumb DOM queries to one per animation frame
    if (!breadcrumbRafId) {
      breadcrumbRafId = requestAnimationFrame(() => {
        updateBreadcrumb();
        breadcrumbRafId = null;
      });
    }

    if (showScrollToTop) {
      enableScrollToTop();

      if (isMobileDevice) return;
      setActionBarPosition(true); // Detach action bar
    } else {
      disableScrollToTop();

      if (isMobileDevice) return;
      setActionBarPosition(false); // Attach action bar
    }
  }

  function handleQuestHover(
    quest: Quest,
    expansionName: string,
    questGroupName: string,
  ): void {
    isHoveringQuest = true;
    hoverOverrideExpansion = expansionName;

    // Format quest group name, removing expansion prefix
    const formattedQuestGroup = formatIdToTitle(
      `questgroup-${questGroupName.toLowerCase().replace(/\s/g, "-")}`,
      "questgroup",
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
    type: "expansion" | "questgroup",
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
    threshold: number,
  ): string {
    const questGroupHeaders = expansionElement.querySelectorAll(
      '[id^="questgroup-"] > summary',
    );

    let lastActiveQuestGroup = "";

    // Check all quest groups and keep track of the last one that's out of view
    for (const header of questGroupHeaders) {
      if (isElementOutOfView(header, threshold)) {
        const questGroupElement = header.closest(
          '[id^="questgroup-"]',
        ) as HTMLElement;
        const questGroupName = formatIdToTitle(
          questGroupElement.id,
          "questgroup",
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
      '[id^="expansion-"] > summary',
    );

    for (const header of expansionHeaders) {
      if (isElementOutOfView(header, SCROLL_THRESHOLD)) {
        hasScrolledPastAnyHeader = true;

        const expansionElement = header.closest(
          '[id^="expansion-"]',
        ) as HTMLElement;
        currentExpansion = formatIdToTitle(expansionElement.id, "expansion");

        // Find the active quest group within this expansion
        currentQuestGroup = findActiveQuestGroup(
          expansionElement,
          SCROLL_THRESHOLD,
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
        "Cancel",
      );

      return;
    }

    updateQuest(quest, input.checked);
  }

  function handleSearchInput(event: CustomEvent) {
    searchQuery = event.detail; // Update the search query
    debouncedFilterQuests(); // Trigger the debounced filter
  }

  function delay(ms: number) {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  async function initProgress() {
    if (hasSharedProgress()) {
      await loadSharedProgress();
    }
    initAllExpansionProgress();
  }

  function initQuests(loadedQuests: ExpansionsQuests) {
    quests.set(loadedQuests);
    filteredQuests.set(loadedQuests);
    closeExpansionAndQuestGroups();
  }

  function initBackground() {
    updateBackground();
  }

  // Handle window resize to update action bar position
  function handleResize() {
    isMobileDevice = isMobile();
    if (isMobileDevice) {
      setActionBarPosition(false);
    } else if (showScrollToTop) {
      setActionBarPosition(true);
    }
  }

  onMount(async () => {
    const loadedQuests = data.quests;

    // Cache mobile detection result
    isMobileDevice = isMobile();

    // Stage 1: Quests
    initQuests(loadedQuests);
    await delay(200);

    // Stage 2: Progress
    loadingMessage = "Initializing progress... <b>kupo!</b>";
    await initProgress();
    updateLastCheckedQuest();
    updateCurrentExpansion();
    await delay(200);

    // Stage 3: Background
    loadingMessage = "Setting up backgrounds... <b>kupo!</b>";
    initBackground();
    await delay(200);

    // Stage 4: Components
    loadingMessage = "Preparing components... <b>kupo!</b>";
    if (isMobileDevice) {
      setActionBarPosition(false);
    }
    await delay(200); // Yes, i know its a fake loading screen :)

    completeLoading();

    // Events
    const contentContainer = getContentContainer();
    if (contentContainer) {
      contentContainer.addEventListener("scroll", handleScroll);
    }

    window.addEventListener("resize", handleResize);
  });

  onDestroy(() => {
    const contentContainer = getContentContainer();
    if (contentContainer) {
      contentContainer.removeEventListener("scroll", handleScroll);
    }
    if (breadcrumbRafId) cancelAnimationFrame(breadcrumbRafId);
    window.removeEventListener("resize", handleResize);
    debouncedFilterQuests.cancel();
  });

  // Reactively update the background whenever the current expansion or showProgress changes
  $: if ($showProgress || $currentExpansion) updateBackground();
</script>

<svelte:head>
  <title>FFXIV Journey</title>
</svelte:head>

<Modal />

<Title />
{#if $isLoadingQuests}
  <Loading message={loadingMessage} />
{/if}
<div class:hidden={$isLoadingQuests} class:fade-in={!$isLoadingQuests}>
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
      class="hidden sm:block sticky top-0 z-10 mx-4 mb-4 bg-surface-card rounded-lg shadow-md border border-border px-4 py-3 transition-all duration-300"
    >
      <div class="flex items-center text-sm text-themed-tertiary font-medium">
        <svg
          class="w-4 h-4 mr-2 text-themed-muted"
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
          class="text-accent-text font-semibold hover:text-accent-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent rounded transition-colors duration-300"
        >
          {displayExpansion}
        </button>
        {#if displayQuestGroup}
          <svg
            class="w-3 h-3 mx-2 text-themed-muted"
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path
              fill-rule="evenodd"
              d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
              clip-rule="evenodd"
            />
          </svg>
          <span class="text-themed-secondary">{displayQuestGroup}</span>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Expansion Details -->
  {#each $filteredQuests as expansion}
    <details
      id="expansion-{expansion.name.replace(/\s/g, '-').toLowerCase()}"
      class="relative mb-1 sm:mb-4 overflow-visible"
      open={openExpansions[expansion.name]}
      on:toggle={(event) => handleExpansionToggle(expansion.name, event)}
    >
      <summary
        class="flex justify-between items-center text-xl sm:text-2xl font-semibold text-themed-primary cursor-pointer mb-1 sm:mb-4 bg-surface-card rounded-lg p-4 shadow transition-all duration-300 ease-out transform hover:scale-[1.01] hover:shadow-lg hover:z-[3] hover:relative focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent"
      >
        {expansion.name}
        {#if $showProgress && $progress[expansion.name]}
          {#if $progress[expansion.name].percent === 100}
            <img
              bind:this={expansionStatusRefs[expansion.name]}
              src="ffxiv_complete.webp"
              alt="Complete"
              class="w-6 h-6"
            />
            <Tooltip
              targetElement={expansionStatusRefs[expansion.name]}
              text="All quests completed"
              orientation="top"
              offsetY={8}
            />
          {:else}
            <img
              bind:this={expansionStatusRefs[expansion.name]}
              src="ffxiv_incomplete.webp"
              alt="Incomplete"
              class="w-6 h-6"
            />
            <Tooltip
              targetElement={expansionStatusRefs[expansion.name]}
              text="In progress"
              orientation="top"
              offsetY={8}
            />
          {/if}
        {/if}
      </summary>
      {#each Object.keys(expansion.quests) as questGroup (questGroup)}
        <details
          id="questgroup-{expansion.name
            .replace(/\s/g, '-')
            .toLowerCase()}-{questGroup.replace(/\s/g, '-').toLowerCase()}"
          class="ml-6 mb-0.5 sm:mb-2 pl-6"
          open={openQuestGroups[expansion.name][questGroup]}
          on:toggle={(event) =>
            handleQuestGroupToggle(expansion.name, questGroup, event)}
        >
          {#if questGroup !== "Main"}
            <summary
              class="flex justify-between items-center text-xl font-semibold text-themed-tertiary cursor-pointer mb-1 sm:mb-3 bg-surface-card rounded-lg p-4 shadow transition-all duration-300 ease-out transform hover:scale-[1.005] hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent"
            >
              {questGroup}
              {#if $showProgress && $groupProgress[expansion.name]?.[questGroup]}
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
                class="flex flex-col sm:flex-row items-center p-4 bg-surface-card rounded-lg shadow-md hover:shadow-lg transition-shadow border border-border hover:border-accent {highlightedQuestNumber ===
                quest['#']
                  ? 'border-2 border-accent-text animate-flicker'
                  : ''}"
                on:mouseenter={() =>
                  handleQuestHover(quest, expansion.name, questGroup)}
                on:mouseleave={handleQuestHoverEnd}
              >
                {#if $showProgress}
                  <div class="flex-none w-10 sm:w-16 mb-4 sm:mb-0">
                    <input
                      type="checkbox"
                      aria-label="Mark {quest.Name} as completed"
                      class="h-6 w-6 rounded-sm border-border focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent transition-all duration-300"
                      style="accent-color: var(--color-check);"
                      bind:checked={$completedQuests[quest["#"]]}
                      on:change={(e) => handleCheckboxChange(e, quest)}
                    />
                  </div>
                {/if}

                <div class="flex-grow sm:ml-4 text-center sm:text-left">
                  <div
                    class="flex items-center justify-center sm:justify-start"
                  >
                    <details class="inline">
                      <summary
                        class="font-bold text-lg sm:text-xl text-themed-primary cursor-pointer list-none rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent transition-all duration-300"
                        title="Show ID"
                      >
                        {quest.Name}
                      </summary>
                      <p class="text-sm text-themed-faint mt-1 hidden sm:block">
                        ID: {quest.Id}
                      </p>
                    </details>
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
                  {#if isMobileDevice}
                    <a
                      href={getGarlandToolsQuestURLByID(quest["#"])}
                      target="_blank"
                      class="block text-center text-accent underline hover:text-accent-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent rounded transition-all duration-300 mt-1 [@media(min-height:601px)]:block [@media(max-height:600px)]:hidden"
                    >
                      (View on Garland Tools)
                    </a>
                  {/if}
                  <p class="text-sm text-themed-muted mt-1 hidden sm:block">
                    <i>"{sanitizeFFXIVMarkUp(quest.Description)}"</i>
                  </p>
                  <img
                    src={getImageUrl(quest.Image)}
                    alt="Quest journal thumbnail"
                    loading="lazy"
                    class="mt-4 w-44 h-16 rounded-md border border-border shadow-sm hidden sm:block"
                  />
                </div>
                <div class="ml-auto hidden sm:flex sm:items-center">
                  <a
                    href={getGarlandToolsQuestURLByID(quest["#"])}
                    target="_blank"
                    class="inline-flex items-center px-4 py-2 bg-surface-card text-icon border border-border rounded-md text-base font-medium transition-all duration-300 hover:bg-surface-card-hover hover:text-themed-hover focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent whitespace-nowrap"
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
                        stroke="currentColor"
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
                  {#each quest.Unlocks as unlock (unlock.Name)}
                    <div
                      class="flex flex-col items-center p-4 bg-surface-card rounded-lg shadow border border-border-light"
                    >
                      <img
                        src={getImageUrl(unlock.Image)}
                        alt="{unlock.Name} thumbnail"
                        class="w-44 h-16 rounded-md border border-border shadow-sm mb-4 hidden sm:block"
                        loading="lazy"
                      />
                      <p class="font-bold text-themed-primary text-center">
                        {unlock.Name}
                      </p>
                      <p class="text-xs text-themed-faint text-center">
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
        in:fade={FADE_IN}
        out:fade={FADE_OUT}
        class="absolute inset-0"
        style="opacity: {isFiltering ? 0 : 1}; pointer-events: {isFiltering
          ? 'none'
          : 'auto'}"
      >
        <div class="flex justify-center">
          <div class="inline-block p-4 bg-surface-card rounded-lg shadow">
            <p class="text-center text-themed-tertiary">No quests found.</p>
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
</div>

<Footer />
