<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { fade } from "svelte/transition";
  import {
    autoMode,
    toggleAutoMode,
    showScrollToTop,
    showProgress,
    toggleProgressVisibility,
  } from "$lib/stores/actionBarStore";
  import Tooltip from "./Tooltip.svelte";

  const dispatch = createEventDispatcher();

  function onShareProgressClicked() {
    dispatch("generateLink");
  }

  function onScrollToTopClicked() {
    dispatch("scrollToTop");
  }

  function onScrollToLastQuestClicked() {
    dispatch("scrollToLastQuest");
  }

  let tooltipTargetToggle: HTMLElement | null = null;
  let tooltipTargetButton: HTMLElement | null = null;

  export let lastCheckedQuestId: number | null = null;
</script>

<div
  transition:fade
  id="action-bar"
  class="fixed md:absolute top-1 sm:top-2 mt-2 bg-white rounded-lg p-2 sm:p-3 md:p-2 shadow flex items-center justify-between z-50 overflow-auto"
>
  <!-- Toggle Button -->
  <div bind:this={tooltipTargetToggle} class="flex items-center">
    <button
      on:click={toggleAutoMode}
      class={`w-10 h-5 sm:w-12 sm:h-6 flex items-center rounded-full p-1 transition-all duration-300 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 ${
        $autoMode ? "bg-gray-300" : "bg-blue-500"
      }`}
    >
      <div
        class={`h-3.5 w-3.5 sm:h-4 sm:w-4 rounded-full bg-white shadow-md transform transition-transform duration-300 ${
          $autoMode ? "translate-x-0" : "translate-x-5 sm:translate-x-6"
        }`}
      ></div>
    </button>

    <!-- Tooltip for Auto/Manual Mode -->
    <Tooltip
      targetElement={tooltipTargetToggle}
      text={$autoMode ? "Autochecking Quests" : "Manual Quest Checking"}
      inlineMode={true}
      offsetX={5}
    />
  </div>

  <!-- Share progress generate -->
  <button
    on:click={onShareProgressClicked}
    class="inline-flex items-center px-2 py-1 sm:px-4 sm:py-2 bg-white text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap ml-1 sm:ml-2"
  >
    <svg
      class="mr-1"
      width="20px"
      height="20px"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M17.5 14.25C16.9877 14.2518 16.4831 14.3751 16.0276 14.6098C15.5722 14.8445 15.1789 15.1838 14.88 15.6L9.59 13C9.6931 12.6765 9.74704 12.3394 9.75 12C9.74704 11.6605 9.6931 11.3234 9.59 11L14.88 8.39996C15.3362 9.01882 15.9982 9.45467 16.7469 9.62915C17.4957 9.80363 18.2821 9.7053 18.9649 9.35185C19.6477 8.99839 20.182 8.41299 20.4717 7.70086C20.7615 6.98874 20.7878 6.19661 20.5458 5.46685C20.3038 4.7371 19.8095 4.11758 19.1517 3.71967C18.4938 3.32177 17.7156 3.17156 16.9569 3.29605C16.1982 3.42055 15.5089 3.81158 15.0127 4.39886C14.5165 4.98614 14.2461 5.73115 14.25 6.49996C14.2524 6.66775 14.2691 6.83503 14.3 6.99996L8.83 9.74996C8.53061 9.43287 8.16938 9.18052 7.76862 9.00852C7.36787 8.83653 6.9361 8.74853 6.5 8.74996C5.63805 8.74996 4.8114 9.09237 4.2019 9.70187C3.59241 10.3114 3.25 11.138 3.25 12C3.25 12.8619 3.59241 13.6886 4.2019 14.2981C4.8114 14.9076 5.63805 15.25 6.5 15.25C6.9361 15.2514 7.36787 15.1634 7.76862 14.9914C8.16938 14.8194 8.53061 14.5671 8.83 14.25L14.3 17C14.2685 17.1682 14.2518 17.3388 14.25 17.51C14.25 18.1528 14.4406 18.7811 14.7977 19.3156C15.1548 19.85 15.6624 20.2666 16.2563 20.5126C16.8501 20.7586 17.5036 20.8229 18.134 20.6975C18.7645 20.5721 19.3436 20.2626 19.7981 19.8081C20.2526 19.3535 20.5621 18.7744 20.6876 18.144C20.813 17.5136 20.7486 16.8601 20.5026 16.2662C20.2566 15.6724 19.8401 15.1648 19.3056 14.8077C18.7711 14.4506 18.1428 14.26 17.5 14.26V14.25ZM17.5 4.74996C17.8461 4.74996 18.1845 4.8526 18.4722 5.04489C18.76 5.23718 18.9843 5.5105 19.1168 5.83027C19.2492 6.15004 19.2839 6.50191 19.2164 6.84137C19.1488 7.18084 18.9822 7.49266 18.7374 7.7374C18.4927 7.98214 18.1809 8.14881 17.8414 8.21634C17.5019 8.28386 17.1501 8.24921 16.8303 8.11675C16.5105 7.9843 16.2372 7.76 16.0449 7.47221C15.8526 7.18443 15.75 6.84608 15.75 6.49996C15.7526 6.03664 15.9378 5.59305 16.2655 5.26543C16.5931 4.93781 17.0367 4.75259 17.5 4.74996ZM6.5 13.75C6.15388 13.75 5.81554 13.6473 5.52775 13.455C5.23997 13.2627 5.01566 12.9894 4.88321 12.6697C4.75076 12.3499 4.7161 11.998 4.78363 11.6586C4.85115 11.3191 5.01782 11.0073 5.26256 10.7625C5.50731 10.5178 5.81912 10.3511 6.15859 10.2836C6.49806 10.2161 6.84993 10.2507 7.1697 10.3832C7.48947 10.5156 7.76278 10.7399 7.95507 11.0277C8.14736 11.3155 8.25 11.6538 8.25 12C8.24738 12.4633 8.06216 12.9069 7.73454 13.2345C7.40691 13.5621 6.96332 13.7473 6.5 13.75ZM17.5 19.25C17.1539 19.25 16.8155 19.1473 16.5278 18.955C16.24 18.7627 16.0157 18.4894 15.8832 18.1697C15.7508 17.8499 15.7161 17.498 15.7836 17.1586C15.8511 16.8191 16.0178 16.5073 16.2626 16.2625C16.5073 16.0178 16.8191 15.8511 17.1586 15.7836C17.4981 15.7161 17.8499 15.7507 18.1697 15.8832C18.4895 16.0156 18.7628 16.2399 18.9551 16.5277C19.1474 16.8155 19.25 17.1538 19.25 17.5C19.2474 17.9633 19.0622 18.4069 18.7345 18.7345C18.4069 19.0621 17.9633 19.2473 17.5 19.25Z"
        fill="#464455"
      />
    </svg>
    <span class="hidden sm:inline">Share</span>
  </button>

  <!-- Progress Toggle Button -->
  <button
    on:click={toggleProgressVisibility}
    class="flex items-center px-2 py-1 sm:px-4 sm:py-2 bg-white text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap ml-1 sm:ml-2"
  >
    <svg
      class="mr-1 sm:mr-1"
      width="20px"
      height="20px"
      viewBox="0 0 24 24"
      fill="none"
    >
      <g id="Edit / Hide">
        <path
          id="Vector"
          d="M3.99989 4L19.9999 20M16.4999 16.7559C15.1473 17.4845 13.6185 17.9999 11.9999 17.9999C8.46924 17.9999 5.36624 15.5478 3.5868 13.7788C3.1171 13.3119 2.88229 13.0784 2.7328 12.6201C2.62619 12.2933 2.62616 11.7066 2.7328 11.3797C2.88233 10.9215 3.11763 10.6875 3.58827 10.2197C4.48515 9.32821 5.71801 8.26359 7.17219 7.42676M19.4999 14.6335C19.8329 14.3405 20.138 14.0523 20.4117 13.7803L20.4146 13.7772C20.8832 13.3114 21.1182 13.0779 21.2674 12.6206C21.374 12.2938 21.3738 11.7068 21.2672 11.38C21.1178 10.9219 20.8827 10.6877 20.4133 10.2211C18.6338 8.45208 15.5305 6 11.9999 6C11.6624 6 11.3288 6.02241 10.9999 6.06448M13.3228 13.5C12.9702 13.8112 12.5071 14 11.9999 14C10.8953 14 9.99989 13.1046 9.99989 12C9.99989 11.4605 10.2135 10.9711 10.5608 10.6113"
          stroke="#464455"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </g>
    </svg>
    <span class="hidden sm:inline"
      >{$showProgress ? "Hide Progress" : "Show Progress"}</span
    >
  </button>

  <!-- Last Quest Button -->
  <button
    on:click={onScrollToLastQuestClicked}
    class="inline-flex items-center px-2 py-1 sm:px-4 sm:py-2 rounded-md text-base font-medium transition-all duration-300 whitespace-nowrap ml-1 sm:ml-2
    {lastCheckedQuestId === null
      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
      : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500'}"
    disabled={lastCheckedQuestId === null}
    aria-disabled={lastCheckedQuestId === null}
  >
    <svg
      class="mr-1"
      width="20px"
      height="20px"
      viewBox="0 0 24 24"
      fill="none"
    >
      <path
        d="M7 3V21M7 21L3 17M7 21L11 17M14 3H21M14 9H19M14 15H17M14 21H15"
        stroke="#464455"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    <span class="hidden sm:block">Scroll to Current Quest</span>
  </button>

  <!-- Scroll Top -->
  {#if $showScrollToTop}
    <button
      bind:this={tooltipTargetButton}
      on:click={onScrollToTopClicked}
      class="inline-flex items-center px-2 py-1 sm:px-2 sm:py-1 bg-white text-gray-700 border border-gray-300 rounded-md text-base font-medium transition-all duration-300 hover:bg-gray-100 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 whitespace-nowrap ml-1 sm:ml-2 mobile-flash sm:animate-pulse"
    >
      <svg width="20px" height="20px" viewBox="0 0 24 24" fill="none">
        <path
          d="M12 5L12 19M12 5L6 11M12 5L18 11"
          stroke="#464455"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        />
      </svg>
    </button>
    <!-- Tooltip for Scroll to Top -->
    <Tooltip
      targetElement={tooltipTargetButton}
      text="Scroll to Top"
      inlineMode={true}
      offsetX={5}
    />
  {/if}
</div>
