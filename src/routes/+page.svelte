<script lang="ts">
  import "../app.css";
  import { base } from "$app/paths";
  import { slide } from "svelte/transition";
  import type { Quest, Quests } from "$lib/model";

  export let data: { quests: Promise<Quests>; loading: boolean };

  let loading = data.loading;
  let quests: Quests = [];
  let filteredQuests: Quests = [];
  let searchQuery: string = "";
  let currentExpansion: string = "";
  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let completedQuests: Record<number, boolean> = {};
  let progress: Record<
    string,
    { percent: number; completed: number; total: number }
  > = {};

  function resetOpenStates(): void {
    openExpansions = {};
    openLocations = {};

    for (const expansion of quests) {
      openExpansions[expansion.name] = false;
      openLocations[expansion.name] = {};

      for (const location of Object.keys(expansion.quests)) {
        openLocations[expansion.name][location] = false;
      }
    }
  }

  function calculateProgress(expansionName: string) {
    const expansion = quests.find((exp) => exp.name === expansionName);
    if (!expansion) return { percent: 0, completed: 0, total: 0 };

    const questsArray: Quest[] = Object.values(expansion.quests).flat();
    const totalQuests = questsArray.length;
    const completedQuestsCount = questsArray.filter(
      (quest) => completedQuests[quest["#"]]
    ).length;

    const percent =
      totalQuests > 0
        ? Math.floor((completedQuestsCount / totalQuests) * 100)
        : 0;

    return {
      percent,
      completed: completedQuestsCount,
      total: totalQuests,
    };
  }

  function toggleQuestCompletion(quest: Quest, isChecked: boolean): void {
    let questFound = false;

    for (const expansion of quests) {
      const questIds: number[] = Object.values(expansion.quests)
        .flat()
        .map((q) => q["#"]);

      for (let i = 0; i < questIds.length; i++) {
        if (questFound) {
          // Uncheck all quests after the found quest
          completedQuests[questIds[i]] = false;
        } else {
          // Check all quests leading up to and including the found quest
          completedQuests[questIds[i]] = true;
        }

        if (questIds[i] === quest["#"]) {
          questFound = true;

          // If the current quest is unchecked, uncheck it and uncheck all following quests
          if (!isChecked) {
            completedQuests[questIds[i]] = false;
          }
        }
      }
    }

    // Update progress bars for all expansions
    calculateAllProgress();
  }

  function calculateAllProgress(): void {
    for (const expansion of quests) {
      progress[expansion.name] = calculateProgress(expansion.name);
    }
  }

  function filterQuests(): void {
    if (searchQuery.trim() === "") {
      filteredQuests = quests;
      resetOpenStates();
      return;
    }

    filteredQuests = [];
    resetOpenStates();

    for (const expansion of quests) {
      const filteredExpansion = {
        name: expansion.name,
        quests: {} as typeof expansion.quests,
      };

      for (const location of Object.keys(expansion.quests)) {
        const locationQuests = expansion.quests[location].filter((quest) =>
          quest.Name.toLowerCase().includes(searchQuery.toLowerCase())
        );

        if (locationQuests.length > 0) {
          filteredExpansion.quests[location] = locationQuests;
          openExpansions[expansion.name] = true;
          openLocations[expansion.name][location] = true;
        }
      }

      if (Object.keys(filteredExpansion.quests).length > 0) {
        filteredQuests.push(filteredExpansion);
      }
    }
  }

  function getImageUrl(imagePath: string | null): string {
    const placeholderImage = `${base}/default_quest_image.png`;
    if (
      !imagePath ||
      imagePath.trim() === "" ||
      imagePath.includes("000000_hr1")
    ) {
      return placeholderImage;
    }
    try {
      // Validate that there is an image path
      const assetPath = `https://beta.xivapi.com/api/1/asset/${imagePath}?format=png`;
      new URL(assetPath);
      return assetPath;
    } catch {
      return placeholderImage;
    }
  }

  function handleCheckboxChange(event: Event, quest: Quest) {
    const input = event.target as HTMLInputElement;
    toggleQuestCompletion(quest, input.checked);
  }

  function updateBackground(): void {
    const bgImage = currentExpansion
      ? `${base}/background_${currentExpansion.replace(/\s/g, "").toLowerCase()}.jpg`
      : `${base}/background.jpg`;

    const bgElement = document.getElementById("background");
    if (bgElement) {
      bgElement.style.backgroundImage = `url('${bgImage}')`;
    }
  }

  let showTitle = true;
  function toggleTitleVisibility() {
    showTitle = !showTitle;
  }

  let tooltipVisible = false;
  function showTooltip() {
    tooltipVisible = true;
  }
  function hideTooltip() {
    tooltipVisible = false;
  }

  let searchInput: HTMLInputElement;
  ``;
  const handleKeydown = (event: KeyboardEvent) => {
    if (event.key === "/") {
      event.preventDefault(); // Prevent the default '/' action
      searchInput?.focus();
    }
  };
  window.addEventListener("keydown", handleKeydown);

  /**
   * Init
   */
  $: {
    data.quests.then((loadedQuests: Quests) => {
      quests = loadedQuests;
      filteredQuests = loadedQuests;
      resetOpenStates();
      calculateAllProgress();

      // Load always a bit
      setTimeout(() => {
        loading = false;
      }, 250);

      // Show footer after loading
      const footer = document.getElementById("footer");
      if (footer) {
        footer.style.display = "block";
      }
    });
  }
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
{#if !loading}
  <div
    class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg p-4 shadow"
  >
    {#each quests as expansion}
      <div class="flex flex-col items-center">
        <p class="font-semibold text-gray-700">{expansion.name}</p>
        <div
          class="w-full bg-gray-200 rounded-full h-4 relative overflow-hidden shadow-inner"
        >
          <div
            class="h-full rounded-full bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 transition-all duration-700 ease-in-out"
            style="width: {progress[expansion.name]?.percent}%"
          ></div>
          <p
            class="absolute w-full text-center text-xs font-semibold top-0 left-0 text-white"
          >
            {progress[expansion.name]?.completed}/{progress[expansion.name]
              ?.total} ({progress[expansion.name]?.percent}%)
          </p>
        </div>
      </div>
    {/each}
  </div>
{/if}

<!-- Content -->
{#if loading}
  <p class="text-center text-gray-600">
    Perparing your quests... <b>K-kupo!</b>
  </p>
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

  {#each filteredQuests as expansion}
    <details class="mb-8" open={openExpansions[expansion.name]}>
      <summary
        class="text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow"
        on:click={() => {
          currentExpansion = expansion.name;
          updateBackground();
        }}
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
              on:click={() => {
                currentExpansion = expansion.name;
                updateBackground();
              }}
            >
              {location}
            </summary>
          {/if}
          <ul class="space-y-4">
            {#each expansion.quests[location] as quest}
              <li
                class="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200"
              >
                <div class="flex-none w-16">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    checked={completedQuests[quest["#"]] || false}
                    on:change={(e) => handleCheckboxChange(e, quest)}
                  />
                </div>
                <div class="flex-grow ml-4">
                  <p class="font-bold text-xl text-gray-800">{quest.Name}</p>
                  <p class="text-sm text-gray-500 mt-1">ID: {quest.Id}</p>
                  <img
                    src={getImageUrl(quest.Image)}
                    alt="Quest journal thumbnail"
                    loading="lazy"
                    class="mt-4 w-44 h-16 rounded-md border border-gray-300 shadow-sm"
                  />
                </div>
                <div class="ml-auto">
                  <a
                    href={`https://www.garlandtools.org/db/#quest/${quest["#"]}`}
                    target="_blank"
                    class="text-blue-600 hover:underline"
                  >
                    Open in Garland Tools
                  </a>
                </div>
              </li>
            {/each}
          </ul>
        </details>
      {/each}
    </details>
  {/each}

  {#if filteredQuests && filteredQuests.length === 0}
    <p class="text-center text-gray-600">No quests found.</p>
  {/if}
{/if}
