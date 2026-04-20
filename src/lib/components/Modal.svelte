<script lang="ts">
  import { onDestroy } from "svelte";
  import { modalState, closeModal } from "../stores/modalManager";

  function handleConfirm() {
    if ($modalState.onConfirm) $modalState.onConfirm();
    closeModal();
  }

  function handleCancel() {
    if ($modalState.onCancel) $modalState.onCancel();
    closeModal();
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape" && $modalState.allowCancel) {
      handleCancel();
    }
  }

  $: if ($modalState.show) {
    if (typeof document !== "undefined") {
      document.addEventListener("keydown", handleKeydown);
    }
  } else {
    if (typeof document !== "undefined") {
      document.removeEventListener("keydown", handleKeydown);
    }
  }

  onDestroy(() => {
    if (typeof document !== "undefined") {
      document.removeEventListener("keydown", handleKeydown);
    }
  });
</script>

{#if $modalState.show}
  <div
    id="modal"
    class="fixed inset-0 bg-surface-overlay z-50"
    style="display: flex; justify-content: center; align-items: center;"
    role="dialog"
    aria-modal="true"
    aria-labelledby="modal-title"
  >
    <div
      class="bg-surface-card rounded-lg shadow-lg p-6 w-11/12 sm:w-1/3 relative"
    >
      <!-- Close button -->
      {#if $modalState.allowCancel}
        <button
          class="absolute top-2 right-2 text-themed-muted hover:text-themed-tertiary focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent"
          on:click={handleCancel}
          aria-label="Close"
        >
          ✕
        </button>
      {/if}

      <!-- Modal title -->
      <h2 id="modal-title" class="text-xl font-bold mb-4 text-themed-primary">
        {$modalState.title}
      </h2>

      <!-- Modal body -->
      <p class="mb-6 text-themed-tertiary">{$modalState.message}</p>

      <!-- Modal actions -->
      <div class="flex justify-end space-x-4">
        {#if $modalState.allowCancel}
          <button
            class="bg-surface-disabled hover:bg-cancel-hover text-themed-secondary py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent transition-all duration-300"
            on:click={handleCancel}
          >
            {$modalState.cancelLabel}
          </button>
        {/if}
        <button
          class="bg-accent hover:bg-accent-hover text-themed-on-accent py-2 px-4 rounded focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-accent transition-all duration-300"
          on:click={handleConfirm}
        >
          {$modalState.confirmLabel}
        </button>
      </div>
    </div>
  </div>
{/if}
