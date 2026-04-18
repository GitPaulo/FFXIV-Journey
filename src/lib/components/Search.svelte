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
    debounceDelay,
  );

  // Handle input changes
  function handleInput(event: Event) {
    inputValue = (event.target as HTMLInputElement).value;
    debouncedInput();
  }

  // Handle keyboard shortcut to focus on the search bar
  function handleKeydown(event: KeyboardEvent) {
    if (
      event.key === "/" &&
      !event.ctrlKey &&
      !event.metaKey &&
      !event.altKey
    ) {
      const active = document.activeElement;
      const tag = active?.tagName?.toLowerCase();
      if (tag === "input" || tag === "textarea" || tag === "select") return;
      event.preventDefault();
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
    type="search"
    aria-label="Search quests"
    placeholder={isMobile() ? "Search quests..." : placeholder}
    class="p-3 pl-10 border border-border rounded-lg w-full bg-surface-input text-themed-primary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent transition-all duration-300 placeholder:text-themed-muted"
    bind:value={inputValue}
    bind:this={searchInput}
    on:input={handleInput}
  />
  <svg
    xmlns="http://www.w3.org/2000/svg"
    xmlns:xlink="http://www.w3.org/1999/xlink"
    version="1.1"
    class="absolute top-1/2 left-3 transform -translate-y-1/2 fill-search-icon pointer-events-none"
    aria-hidden="true"
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
