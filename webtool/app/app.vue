<script setup lang="ts">
useHead({
  meta: [
    { name: 'viewport', content: 'width=device-width, initial-scale=1' }
  ],
  link: [
    { rel: 'icon', href: '/favicon.ico' }
  ],
  htmlAttrs: {
    lang: 'en'
  }
})

const title = 'DSM Test Suite'
const description = 'DSM Test Suite for testing and evaluating P2P networks.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  ogImage: 'https://ui.nuxt.com/assets/templates/nuxt/starter-light.png',
  twitterCard: 'summary_large_image'
})

const groupStore = useGroupStore()
const activeGroup = computed(() => groupStore.activeGroup)

onMounted(async () => {
  await groupStore.fetchGroups()
  groupStore.startHealthUpdates()
})
onBeforeUnmount(() => groupStore.stopHealthUpdates())

</script>

<template>
  <UApp>
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
    <GroupSelectionModal v-if="activeGroup === null" />
  </UApp>
</template>
