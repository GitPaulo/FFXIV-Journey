<script lang="ts">
  export let message: string =
    "Please wait, i'm preparing your quests... <b>kupo!</b>";
</script>

<div
  class="bg-surface-card p-4 rounded-lg shadow-md max-w-max mx-auto"
  role="status"
  aria-live="polite"
>
  <img
    src="loading.gif"
    alt="Loading"
    class="mx-auto p-4"
    style="margin-left: 7rem;"
  />
  <p class="text-center text-themed-tertiary p-3">
    {@html message}
  </p>
</div>
