<template>
  <UModal
    v-model:open="open"
    title="Put image"
    :dismissible="!loading"
  >
    <UButton
      icon="lucide-image-plus"
      label="Put image"
      variant="soft"
      @click="openModal"
    />
    <template #content>
      <UCard>
        <template #header>
          <div class="font-semibold">
            Put image
          </div>
        </template>
        <form
          class="flex flex-col gap-3"
          @submit.prevent="submit"
        >
          <UFormField label="Peer" required>
            <NetworkPeerSelect
              v-model="peerId"
              :peers="peers"
              placeholder="Select a peer"
              :disabled="loading"
            />
          </UFormField>
          <UFormField label="Image ID" required>
            <UInput
              v-model="imageId"
              placeholder="image-0.png"
              class="w-full"
              :disabled="loading"
            />
            <template #help>
              <UtilHashHint :value="imageId" />
            </template>
          </UFormField>
          <UFormField label="PNG file" :error="fileError" required>
            <UFileUpload
              v-model="file"
              accept=".png,image/png"
              label="Choose a PNG file"
              :file-image="false"
              :disabled="loading"
            />
          </UFormField>
          <img
            v-if="preview"
            :key="preview"
            :src="preview"
            alt="Selected image preview"
            class="max-h-48 max-w-full self-center object-contain"
            @load="previewLoaded"
            @error="invalidPreview"
          >
          <UButton
            type="submit"
            label="Put image"
            :loading="loading"
            :disabled="!canSubmit || reading"
          />
        </form>
      </UCard>
    </template>
  </UModal>
</template>

<script setup lang="ts">
import { putPeerImage } from '~~/app/services/backend/proxy.service'
import { readPngAsBase64 } from '~/utils/png'
import type { TopologyPeer } from '~/composables/useNetworkTopology'

const props = defineProps<{
  networkId: string
  peers: TopologyPeer[]
  selectedPeer: string | null
}>()

const open = ref(false)
const peerId = ref('')
const imageId = ref('')
const file = ref<File | null>(null)
const image = ref('')
const previewReady = ref(false)
const fileError = ref('')
const reading = ref(false)
const loading = ref(false)
let defaultImageId = ''
const preview = computed(() => image.value ? `data:image/png;base64,${image.value}` : '')
const canSubmit = computed(() => !!imageId.value.trim() && !!image.value && previewReady.value
  && props.peers.some(peer => peer.peerId === peerId.value))

watch(file, async (selected, _previous, onCleanup) => {
  image.value = ''
  previewReady.value = false
  fileError.value = ''
  reading.value = !!selected
  if (!selected) return
  if (!imageId.value.trim() || imageId.value === defaultImageId) {
    imageId.value = selected.name
    defaultImageId = selected.name
  }
  let active = true
  onCleanup(() => { active = false })
  try {
    const result = await readPngAsBase64(selected)
    if (active) image.value = result
  } catch (error) {
    if (active) fileError.value = error instanceof Error ? error.message : String(error)
  } finally {
    if (active) reading.value = false
  }
}, { flush: 'sync' })

function previewLoaded(event: Event) {
  if (event.currentTarget instanceof HTMLImageElement && event.currentTarget.getAttribute('src') === preview.value) {
    previewReady.value = true
  }
}

function invalidPreview(event: Event) {
  if (!(event.currentTarget instanceof HTMLImageElement) || event.currentTarget.getAttribute('src') !== preview.value) return
  image.value = ''
  previewReady.value = false
  fileError.value = 'Could not preview PNG file'
}

function openModal() {
  peerId.value = props.peers.some(peer => peer.peerId === props.selectedPeer) ? props.selectedPeer ?? '' : ''
  imageId.value = ''
  defaultImageId = ''
  file.value = null
  open.value = true
}

async function submit() {
  if (!canSubmit.value || reading.value || loading.value) return
  loading.value = true
  try {
    await putPeerImage(props.networkId, peerId.value, imageId.value, image.value)
    useToast().add({
      title: 'Image accepted',
      description: 'The peer acknowledged the image; storage may still be in progress.',
      color: 'success'
    })
    open.value = false
  } catch (error) {
    useToast().add({
      title: 'Failed to put image',
      description: error instanceof Error ? error.message : String(error),
      color: 'error'
    })
  } finally {
    loading.value = false
  }
}
</script>
