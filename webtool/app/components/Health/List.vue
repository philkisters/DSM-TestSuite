<template>
  <div class="flex gap-2">
    <HealthOrchestrator v-for="group in groups" :group="group" :active="group.id === activeGroupId" :key="group.id" />
  </div>
</template>
<script setup lang="ts">
const groupStore = useGroupStore()
const groups = computed(() => groupStore.groups)
const activeGroupId = computed(() => groupStore.activeGroup?.id)

</script>