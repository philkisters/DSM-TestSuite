<template>
  <div class="h-screen w-screen overflow-hidden flex-col">
    <UHeader>
      <template #left>
        <NuxtLink
          to="/"
          class="focus-visible:outline-3 outline-primary/25 rounded-md p-1 -ms-1 flex"
        >
          <AppLogo class="w-auto h-6 shrink-0" />
          <span class="ml-2 text-xl font-bold">
            DSM-TestSuite
          </span>
          <span v-if="activeGroup" class="ml-4 text-xl text-primary" @click="removeActiveGroup()">
            {{ activeGroup.name }}
          </span>
        </NuxtLink>
      </template>
    
      <template #right>
        <HealthList />
        <UColorModeButton />
    
        <UButton
          to="https://git.informatik.uni-hamburg.de/dos/teaching/dsm-26"
          target="_blank"
          icon="i-simple-icons-gitlab"
          aria-label="DSM-GitLab"
          color="secondary"
          variant="ghost"
        />
      </template>
    </UHeader>
    <div v-if="!initialized" class="p-6 text-3xl">
      <UiLoading text="Initializing TestSuite..." :size="8" />
    </div>
    <div v-else class="flex h-[calc(100vh-63px)]">
      <div class="flex flex-col border-r-muted border-r-1">
        <NuxtLink
          active-class="bg-secondary/30"
          to="/"
        >
          <PanelButton>
            Dashboard
          </PanelButton>
        </NuxtLink>
        <NuxtLink
          active-class="bg-secondary/30"
          to="/challenges"
        >
          <PanelButton>
            Challenges
          </PanelButton>
        </NuxtLink>
        <NuxtLink
          active-class="bg-secondary/30"
          to="/networks"
        >
          <PanelButton>
            Networks
          </PanelButton>
        </NuxtLink>
      </div>
      <slot />
    </div>
  </div>
</template>
<script setup lang="ts">
const groupStore = useGroupStore()

const initialized = computed(() => groupStore.initialized)

const removeActiveGroup = () => {
  useRouter().push('/').then(() => {
    groupStore.removeActiveGroup()
  })
}

const activeGroup = computed(() => groupStore.activeGroup)
</script>