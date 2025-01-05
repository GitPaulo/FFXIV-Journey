<script>
  export let quests;
  export let progress;
</script>

<div
  class="mb-6 grid grid-cols-1 md:grid-cols-2 gap-4 bg-white rounded-lg p-4 shadow"
>
  {#each $quests as expansion}
    <div class="flex flex-col items-center">
      <p class="font-semibold text-gray-700">
        {expansion.name}<span class="inline sm:hidden ml-1"
          >({$progress[expansion.name]?.completed}/{$progress[expansion.name]
            ?.total})</span
        >
      </p>
      <div
        class="hidden sm:block w-full bg-gray-200 rounded-full h-4 relative overflow-hidden shadow-inner"
      >
        <div
          class="h-full rounded-full bg-gradient-to-r from-blue-500 via-blue-600 to-blue-700 transition-all duration-700 ease-in-out"
          style="width: {$progress[expansion.name]?.percent}%"
        ></div>
        <p
          class="absolute w-full text-center text-xs font-semibold top-0 left-0 text-white"
        >
          {$progress[expansion.name]?.completed}/{$progress[expansion.name]
            ?.total} ({$progress[expansion.name]?.percent}%)
        </p>
      </div>
    </div>
  {/each}
</div>
