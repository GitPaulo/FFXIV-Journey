<script lang="ts">
  import { modalState, closeModal } from "../stores/modalManager";

  function handleConfirm() {
    if ($modalState.onConfirm) $modalState.onConfirm();
    closeModal();
  }

  function handleCancel() {
    if ($modalState.onCancel) $modalState.onCancel();
    closeModal();
  }
</script>

{#if $modalState.show}
  <div
    id="modal"
    class="fixed inset-0 bg-gray-600 bg-opacity-50 z-50"
    style="display: flex; justify-content: center; align-items: center;"
  >
    <div
      class="bg-white rounded-lg shadow-lg p-6 w-11/12 sm:w-1/3 relative"
      style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);"
    >
      <!-- Close button -->
      {#if $modalState.allowCancel}
        <button
          class="absolute top-2 right-2 text-gray-400 hover:text-gray-600 focus:outline-none"
          on:click={handleCancel}
        >
          ✕
        </button>
      {/if}

      <!-- Modal title -->
      <h2 class="text-xl font-bold mb-4 text-gray-800">{$modalState.title}</h2>

      <!-- Modal body -->
      <p class="mb-6 text-gray-600">{$modalState.message}</p>

      <!-- Modal actions -->
      <div class="flex justify-end space-x-4">
        {#if $modalState.allowCancel}
          <button
            class="bg-gray-300 hover:bg-gray-400 text-gray-700 py-2 px-4 rounded"
            on:click={handleCancel}
          >
            {$modalState.cancelLabel}
          </button>
        {/if}
        <button
          class="bg-blue-500 hover:bg-blue-600 text-white py-2 px-4 rounded"
          on:click={handleConfirm}
        >
          {$modalState.confirmLabel}
        </button>
      </div>
    </div>
  </div>
{/if}
