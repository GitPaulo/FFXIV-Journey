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

  export function clear() {
    searchInput.value = "";
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
    class="p-3 pl-10 border border-gray-300 rounded-lg w-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all duration-300"
    bind:value={inputValue}
    bind:this={searchInput}
    on:input={handleInput}
  />
  <svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    version="1.1"
    class="absolute top-1/2 left-3 transform -translate-y-1/2 fill-gray-300 pointer-events-none"
    width="24px"
    height="24px"
    viewBox="0 0 24 24"
    ><path
      d="M19 3H5C3.9 3 3 3.9 3 5V19C3 20.1 3.9 21 5 21H19C20.1 21 21 20.1 21 19V5C21 3.9 20.1 3 19 3M9.3 19H7L14.7 5H17L9.3 19Z"
      stroke-linejoin="round"
      stroke-linecap="round"
    /></svg
  >
</div>
