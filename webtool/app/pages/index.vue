<template>
  <div class="flex-1 min-h-0 overflow-y-auto p-4">
    <div class="flex flex-col justify-start items-center w-full">
      <h1 class="text-center text-4xl font-bold mt-4">Group Stats</h1>
      <div v-if="activeGroupName !== 'Guest'" class="w-full">
        <USeparator class="my-4" />
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4 place-items-center" v-if="showGroupHealth">
          <GroupHealthUptime v-for="group in groups" :key="group.id" :groupId="group.id" :groupName="group.name">
            <GroupChallengeSummary :group-id="group.id" />
          </GroupHealthUptime>
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

const showGroupHealth = ref(true)

const activeGroupName = computed(() => groupStore.activeGroup?.name ?? 'Guest')
</script>
