<script>
  import { slide } from "svelte/transition";
  import { loading } from "../stores/questsStore";
  import {
    showHideTooltip,
    enableHideTooltip,
    disableHideTooltip,
  } from "$lib/stores/titleStore";
</script>

{#if $loading}
  <div
    class="relative flex flex-col mb-8 justify-center items-center"
    transition:slide
  >
    <div class="bg-white rounded-lg p-2 shadow max-w-xl w-full relative">
      <!-- Hide Button -->
      <button
        on:mouseover={enableHideTooltip}
        on:focus={enableHideTooltip}
        on:mouseleave={disableHideTooltip}
        on:blur={disableHideTooltip}
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
        {#if showHideTooltip}
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

      <h3
        class="hidden sm:block font-bold text-center text-gray-600 mt-4 text-lg"
      >
        Track your main story quest journey with the utmost ease.
      </h3>
    </div>
  </div>
{:else}
  <div class="flex justify-end my-2">
    <div
      class="group flex items-center p-3 bg-white rounded-lg shadow relative transition-all duration-300"
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
