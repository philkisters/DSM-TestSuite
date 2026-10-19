<template>
  <div class="flex flex-grow">
    <div class="flex flex-col text-center justify-start w-full">
      <h1 class="text-center text-4xl font-bold my-4">Welcome  {{ activeGroupName }}</h1>
      <p class="text-center text-2xl">
        Some day, you will find awesome stats about your group, <br> orchestrator and challenges here on this really cool page!
      </p>
    </div>

  </div>
</template>
<script setup lang="ts">
const groupStore = useGroupStore()

const activeGroupName = computed(() => groupStore.activeGroup?.name ?? 'Guest')
</script>
