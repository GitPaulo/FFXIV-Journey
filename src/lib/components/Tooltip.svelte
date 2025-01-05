<script lang="ts">
  import { fade } from "svelte/transition";
  import { onDestroy } from "svelte";

  export let text: string;
  export let targetElement: HTMLElement | null = null;
  export let offsetX: number = 0;
  export let offsetY: number = 0;
  export let orientation: "top" | "bottom" | "left" | "right" = "top";
  export let inlineMode: boolean = false;

  let tooltipElement: HTMLElement | null = null;
  let showTooltip = false;
  let style = "";

  function handleMouseOver() {
    showTooltip = true;
  }

  function handleMouseLeave() {
    showTooltip = false;
  }

  // Attach and detach event listeners dynamically when `targetElement` changes
  let currentTarget: HTMLElement | null = null;

  $: {
    // Detach event listeners from the previous target
    if (currentTarget) {
      console.log(
        "Removing event listeners from currentTarget:",
        currentTarget
      );
      currentTarget.removeEventListener("mouseover", handleMouseOver);
      currentTarget.removeEventListener("mouseleave", handleMouseLeave);
    }

    // Attach event listeners to the new target
    if (targetElement) {
      console.log("Attaching event listeners to targetElement:", targetElement);
      targetElement.addEventListener("mouseover", handleMouseOver);
      targetElement.addEventListener("mouseleave", handleMouseLeave);
      currentTarget = targetElement; // Track the current target for cleanup
    }
  }

  onDestroy(() => {
    if (currentTarget) {
      currentTarget.removeEventListener("mouseover", handleMouseOver);
      currentTarget.removeEventListener("mouseleave", handleMouseLeave);
    }
  });

  // Dynamically calculate tooltip position
  $: if (!inlineMode && targetElement && tooltipElement) {
    const rect = targetElement.getBoundingClientRect();
    const tooltipRect = tooltipElement.getBoundingClientRect();

    switch (orientation) {
      case "top":
        style = `top: ${rect.top + window.scrollY - tooltipRect.height - offsetY}px; 
                 left: ${rect.left + window.scrollX + rect.width / 2 - tooltipRect.width / 2 + offsetX}px;`;
        break;
      case "bottom":
        style = `top: ${rect.bottom + window.scrollY + offsetY}px; 
                 left: ${rect.left + window.scrollX + rect.width / 2 - tooltipRect.width / 2 + offsetX}px;`;
        break;
      case "left":
        style = `top: ${rect.top + window.scrollY + rect.height / 2 - tooltipRect.height / 2 + offsetY}px; 
                 left: ${rect.left + window.scrollX - tooltipRect.width - offsetX}px;`;
        break;
      case "right":
        style = `top: ${rect.top + window.scrollY + rect.height / 2 - tooltipRect.height / 2 + offsetY}px; 
                 left: ${rect.right + window.scrollX + offsetX}px;`;
        break;
    }
  }
</script>

{#if showTooltip}
  {#if inlineMode}
    <span
      transition:fade
      class="bg-gray-800 text-white text-xs rounded px-2 py-1 shadow-lg z-50"
      style="margin-top: {offsetY}px; margin-left: {offsetX}px;"
    >
      {text}
    </span>
  {:else}
    <div
      transition:fade
      bind:this={tooltipElement}
      class="bg-gray-800 text-white text-xs rounded px-2 py-1 shadow-lg z-50 fixed"
      {style}
    >
      {text}
    </div>
  {/if}
{/if}
