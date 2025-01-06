<script lang="ts">
  import { createEventDispatcher, onMount, onDestroy } from "svelte";
  import { fade } from "svelte/transition";

  export let placeholder: string = "Search...";
  export let value: string = "";
  export let debounceDelay: number = 150;

  const dispatch = createEventDispatcher();

  let inputValue = value;
  let searchInput: HTMLInputElement;

  // Debounce helper
  import { debounce } from "lodash";
  import { isMobile } from "$lib/utils";
  const debouncedInput = debounce(
    () => dispatch("input", inputValue),
    debounceDelay
  );

  // Handle input changes
  function handleInput(event: Event) {
    inputValue = (event.target as HTMLInputElement).value;
    debouncedInput();
  }

  // Handle keyboard shortcut to focus on the search bar
  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "/") {
      event.preventDefault(); // Prevent the default '/' action
      searchInput?.focus();
    }
  }

  onMount(() => {
    window.addEventListener("keydown", handleKeydown);
  });

  onDestroy(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
</script>

<div transition:fade class="mb-6 flex relative">
  <input
    type="text"
    placeholder={isMobile() ? "Search quests..." : placeholder}
    class="p-3 pl-10 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-blue-500"
    bind:value={inputValue}
    bind:this={searchInput}
    on:input={handleInput}
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
