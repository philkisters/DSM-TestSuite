<template>
  <div class="flex flex-grow p-4">
    <div class="flex flex-col justify-start items-center w-full">
      <h1 class="text-center text-4xl font-bold mt-4">Welcome  {{ activeGroupName }}</h1>
      <div v-if="activeGroupName !== 'Guest'" class="w-full">
        <USeparator class="my-4" />
        <h3 class="text-center text-2xl font-semibold">
          Group Uptime
        </h3>
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <GroupHealthUptime v-for="group in groups" :key="group.id" :groupId="group.id" :groupName="group.name" />
        </div>
      </div>
      <div v-else>
        <UiLoading text="Loading group data..." />
      </div>
    </div>
    
  </div>
</template>
<script setup lang="ts">
const groupStore = useGroupStore()

const groups = computed(() => groupStore.groups)

const activeGroupName = computed(() => groupStore.activeGroup?.name ?? 'Guest')
</script>
