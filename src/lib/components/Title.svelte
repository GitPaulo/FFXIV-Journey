<script>
  import { slide } from "svelte/transition";
  import { isLoadingQuests } from "../stores/questsStore";
</script>

{#if $isLoadingQuests}
  <div class="relative flex flex-col mb-8 justify-center items-center">
    <div class="bg-white rounded-lg p-6 shadow w-full relative max-w-fit">
      <div class="text-center">
        <img src="logo.png" alt="FFXIV Journey" class="h-16 mx-auto" />
        <h1 class="text-2xl sm:text-3xl font-bold text-blue-600 mt-2">
          FFXIV Journey Tracker
        </h1>
      </div>

      <h3
        class="hidden sm:block font-bold text-center text-gray-600 mt-4 text-lg"
      >
        Track your main story quest journey with the utmost ease.
      </h3>
    </div>
  </div>
{:else}
  <div class="hidden sm:flex justify-end my-2">
    <div
      class="group flex items-center p-3 bg-white rounded-lg shadow relative transition-all duration-300"
      transition:slide
    >
      <h1
        class="text-blue-600 text-lg font-bold opacity-0 transform scale-95 hidden group-hover:block group-hover:opacity-100 group-hover:scale-100 transition-all duration-300"
      >
        FFXIV Journey Tracker
      </h1>
      <img src="logo.png" alt="FFXIV Journey" class="h-16" />
    </div>
  </div>
{/if}
