<template>
  <div class="min-h-0 flex-1 flex flex-col">
    <div class="flex flex-wrap items-center gap-2 py-2">
      <UtilIdentifier :id="peerId" class="flex-1" />
      <UBadge :color="peer ? 'success' : 'neutral'" variant="subtle">
        {{ peer ? 'Active' : 'Unknown' }}
      </UBadge>
      <UButton color="warning" :loading="busy === 'leave'" :disabled="busy !== null" @click="emit('leave')">
        Leave
      </UButton>
      <UButton color="error" :loading="busy === 'kill'" :disabled="busy !== null" @click="emit('kill')">
        Kill
      </UButton>
    </div>
    <div class="grid grid-cols-2 gap-4 py-2">
      <div class="flex min-w-0 items-center gap-2">
        <UIcon name="lucide-arrow-left" class="shrink-0" aria-hidden="true" />
        <div class="min-w-0">
          <div class="text-muted text-sm">
            Predecessor
          </div>
          <UtilIdentifier v-if="peer?.predecessor" :id="peer.predecessor" />
          <span v-else class="text-muted">-</span>
        </div>
      </div>
      <div class="flex min-w-0 items-center justify-end gap-2">
        <div class="min-w-0 text-right">
          <div class="text-muted text-sm">
            Successor
          </div>
          <UtilIdentifier v-if="peer?.successor" :id="peer.successor" />
          <span v-else class="text-muted">-</span>
        </div>
        <UIcon name="lucide-arrow-right" class="shrink-0" aria-hidden="true" />
      </div>
    </div>
    <div class="flex items-center justify-between gap-2 pt-2">
      <div class="font-semibold">
        Images ({{ images?.length ?? '?' }})
      </div>
      <UButton
        label="Load"
        size="sm"
        variant="soft"
        :loading="loading"
        :disabled="!images?.length || loading"
        @click="loadImages"
      />
    </div>
    <div class="min-h-0 flex-1 overflow-y-auto">
      <div v-if="images === undefined" class="text-muted py-2">
        Image list not loaded.
      </div>
      <div v-else-if="!images.length" class="text-muted py-2">
        No images.
      </div>
      <ul v-else class="space-y-2 py-2">
        <li v-for="(image, index) in images" :key="`${image}-${index}`" class="flex items-center gap-3">
          <img
            v-if="loadedImages.get(image)"
            :src="`data:image/png;base64,${loadedImages.get(image)}`"
            :alt="image"
            class="size-12 shrink-0 object-contain"
          >
          <div v-else class="flex size-12 shrink-0 items-center justify-center rounded border border-default" aria-hidden="true">
            <UIcon name="lucide-image" />
          </div>
          <div class="min-w-0">
            <UtilIdentifier :id="image" />
            <div v-if="imageErrors.get(image)" class="text-error text-xs">
              {{ imageErrors.get(image) }}
            </div>
          </div>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { getPeerImage } from '~~/app/services/backend/proxy.service'
import type { TopologyPeer } from '~/composables/useNetworkTopology'

const props = defineProps<{
  networkId: string
  peerId: string
  peer: TopologyPeer | null
  images: string[] | undefined
  busy: 'leave' | 'kill' | null
}>()
const emit = defineEmits<{ leave: [], kill: [] }>()
const loadedImages = shallowRef<ReadonlyMap<string, string>>(new Map())
const imageErrors = shallowRef<ReadonlyMap<string, string>>(new Map())
const loading = ref(false)
let controller: AbortController | null = null

function resetImages() {
  controller?.abort()
  controller = null
  loading.value = false
  loadedImages.value = new Map()
  imageErrors.value = new Map()
}

watch([() => props.networkId, () => props.peerId, () => props.images], resetImages, { flush: 'sync' })
onScopeDispose(resetImages)

async function loadImages() {
  if (loading.value || !props.images?.length) return
  const request = new AbortController()
  controller = request
  loading.value = true
  imageErrors.value = new Map()
  const ids = [...new Set(props.images)].filter(id => !loadedImages.value.has(id))
  const networkId = props.networkId
  const peerId = props.peerId

  async function loadNext() {
    while (ids.length && !request.signal.aborted) {
      const id = ids.shift()!
      try {
        const image = await getPeerImage(networkId, peerId, id, request.signal)
        if (!request.signal.aborted) loadedImages.value = new Map(loadedImages.value).set(id, image)
      } catch (error) {
        if (!request.signal.aborted) {
          imageErrors.value = new Map(imageErrors.value).set(id, error instanceof Error ? error.message : String(error))
        }
      }
    }
  }

  try {
    await Promise.all(Array.from({ length: Math.min(4, ids.length) }, () => loadNext()))
  } finally {
    if (controller === request) {
      controller = null
      loading.value = false
    }
  }
}
</script>
