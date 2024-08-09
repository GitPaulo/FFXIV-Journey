<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import type { Quest, FilteredQuests, Expansions } from "$lib/model";

  let expansions: Expansions = {};
  let filteredQuests: FilteredQuests = {};
  let searchQuery = "";
  let loading = true;

  const dispatch = createEventDispatcher();
  const placeholderImage = "/default_quest_image.png";

  let openExpansions: Record<string, boolean> = {};
  let openLocations: Record<string, Record<string, boolean>> = {};
  let completedQuests: Record<number, boolean> = {};

  let currentExpansion = "";

  onMount(async () => {
    await fetchQuests();
    updateBackground();
  });

  async function fetchQuests(): Promise<void> {
    try {
      const response = await fetch("/Quests.json");
      const data = await response.json();
      expansions = data.expansions;
      filteredQuests = expansions;
      resetOpenStates();
    } catch (error) {
      console.error("Error loading quests:", error);
    } finally {
      loading = false;
    }
  }

  function updateBackground(): void {
    if (typeof document !== "undefined") {
      const bgImage = currentExpansion
        ? `/background_${currentExpansion.replace(/\s/g, "").toLowerCase()}.jpg`
        : "/background.jpg";
      const bgElement = document.getElementById("background");
      if (bgElement) {
        bgElement.style.backgroundImage = `url('${bgImage}')`;
      }
    }
  }

  function getImageUrl(imagePath: string | null): string {
    return imagePath
      ? `https://beta.xivapi.com/api/1/asset/${imagePath}?format=png`
      : placeholderImage;
  }

  function resetOpenStates(): void {
    openExpansions = {};
    openLocations = {};

    for (const expansion of Object.keys(expansions)) {
      openExpansions[expansion] = false;
      openLocations[expansion] = {};

      for (const location of Object.keys(expansions[expansion])) {
        openLocations[expansion][location] = false;
      }
    }
  }

  function calculateProgress(expansion: string): {
    percent: number;
    completed: number;
    total: number;
  } {
    const quests = Object.values(expansions[expansion]).flat();
    const totalQuests = quests.length;
    const completedQuestsCount = quests.filter(
      (quest) => completedQuests[quest["#"]]
    ).length;

    const percent = Math.floor((completedQuestsCount / totalQuests) * 100);
    return { percent, completed: completedQuestsCount, total: totalQuests };
  }

  function toggleQuestCompletion(quest: Quest, isChecked: boolean): void {
    const questIds = Object.values(expansions[quest.Expansion])
      .flat()
      .map((q) => q["#"]);
    const questIndex = questIds.indexOf(quest["#"]);

    if (isChecked) {
      for (let i = 0; i <= questIndex; i++) {
        completedQuests[questIds[i]] = true;
      }
    } else {
      for (let i = questIndex; i < questIds.length; i++) {
        completedQuests[questIds[i]] = false;
      }
    }

    if (isChecked) {
      const expansionsList = Object.keys(expansions);
      const currentExpansionIndex = expansionsList.indexOf(quest.Expansion);
      for (let i = 0; i <= currentExpansionIndex; i++) {
        const previousExpansion = expansionsList[i];
        Object.values(expansions[previousExpansion])
          .flat()
          .forEach((prevQuest) => {
            completedQuests[prevQuest["#"]] = true;
          });
      }
    }

    calculateAllProgress();
  }

  function calculateAllProgress(): void {
    for (const expansion of Object.keys(expansions)) {
      calculateProgress(expansion);
    }
  }

  function filterQuests(): void {
    if (searchQuery.trim() === "") {
      filteredQuests = expansions;
      resetOpenStates();
      return;
    }

    filteredQuests = {};
    resetOpenStates();

    for (const expansion of Object.keys(expansions)) {
      for (const location of Object.keys(expansions[expansion])) {
        const quests = expansions[expansion][location].filter((quest: Quest) =>
          quest.Name.toLowerCase().includes(searchQuery.toLowerCase())
        );

        if (quests.length > 0) {
          if (!filteredQuests[expansion]) {
            filteredQuests[expansion] = {};
            openExpansions[expansion] = true;
          }

          filteredQuests[expansion][location] = quests;
          openLocations[expansion][location] = true;
        }
      }
    }
  }

  function lazyLoadImage(node: HTMLImageElement): {
    destroy(): void;
  } {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          node.src = node.dataset.src!;
          observer.unobserve(node);
        }
      },
      {
        rootMargin: "100px",
      }
    );
    observer.observe(node);
    return {
      destroy() {
        observer.unobserve(node);
      },
    };
  }
</script>

<div class="flex flex-col mb-8 justify-center items-center">
  <div class="bg-white rounded-lg p-6 shadow max-w-xl w-full">
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

{#if !loading && currentExpansion}
  <div
    class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg p-4 shadow"
  >
    {#each Object.keys(expansions) as expansion}
      <div
        class="flex flex-col items-center"
        on:click={() => {
          currentExpansion = expansion;
          updateBackground();
        }}
      >
        <p class="font-semibold text-gray-700">{expansion}</p>
        <div class="w-full bg-gray-200 rounded-full h-4 relative">
          <div
            class="bg-blue-600 h-4 rounded-full absolute"
            style="width: {calculateProgress(expansion).percent}%"
          ></div>
          <p
            class="absolute w-full text-center text-xs font-semibold top-0 left-0"
          >
            {calculateProgress(expansion).completed}/{calculateProgress(
              expansion
            ).total} ({calculateProgress(expansion).percent}%)
          </p>
        </div>
      </div>
    {/each}
  </div>
{/if}

{#if !loading}
  <div class="mb-6">
    <input
      type="text"
      placeholder="Search quests..."
      class="p-3 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
      bind:value={searchQuery}
      on:input={filterQuests}
    />
  </div>
{/if}

{#if loading}
  <p class="text-center text-gray-600">Loading quests...</p>
{:else if Object.keys(filteredQuests).length > 0}
  {#each Object.keys(filteredQuests) as expansion}
    <details class="mb-8" {...openExpansions[expansion] ? { open: true } : {}}>
      <summary
        class="text-2xl font-semibold text-gray-800 cursor-pointer mb-4 bg-white rounded-lg p-4 shadow"
        on:click={() => {
          currentExpansion = expansion;
          updateBackground();
        }}
      >
        {expansion}
      </summary>
      {#each Object.keys(filteredQuests[expansion]) as location}
        <details
          class="ml-6 mb-6 pl-6"
          {...openLocations[expansion][location] ? { open: true } : {}}
        >
          {#if location !== "Main"}
            <summary
              class="text-xl font-semibold text-gray-600 cursor-pointer mb-3 bg-white rounded-lg p-4 shadow"
              on:click={() => {
                currentExpansion = expansion;
                updateBackground();
              }}
            >
              {location}
            </summary>
          {/if}
          <ul class="space-y-4">
            {#each filteredQuests[expansion][location] as quest}
              <li
                class="flex items-center p-4 bg-white rounded-lg shadow hover:shadow-lg transition-shadow border border-gray-200"
              >
                <div class="flex-none w-16">
                  <input
                    type="checkbox"
                    class="form-checkbox h-6 w-6 text-blue-600 rounded focus:ring-2 focus:ring-blue-500"
                    checked={completedQuests[quest["#"]] || false}
                    on:change={(e) =>
                      toggleQuestCompletion(quest, e.target.checked)}
                  />
                </div>
                <div class="flex-grow ml-4">
                  <p class="font-bold text-xl text-gray-800">{quest.Name}</p>
                  <p class="text-sm text-gray-500 mt-1">ID: {quest.Id}</p>
                  <img
                    data-src={getImageUrl(quest.Image)}
                    alt="Quest Icon"
                    class="mt-4 w-16 h-16 rounded-md border border-gray-300 shadow-sm"
                    use:lazyLoadImage
                  />
                </div>
              </li>
            {/each}
          </ul>
        </details>
      {/each}
    </details>
  {/each}
{:else}
  <p class="text-center text-gray-600">No quests found.</p>
{/if}
