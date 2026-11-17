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
      <UCard class="min-h-0 overflow-y-auto">
        <template #header>
          <div class="font-semibold">
            Put image
          </div>
        </template>
        <USwitch
          v-model="multiUpload"
          label="Multi upload"
          class="mb-4"
          :disabled="loading"
        />
        <form
          v-if="multiUpload"
          class="flex flex-col gap-3"
          @submit.prevent="submitMultiple"
        >
          <UFormField
            label="PNG files"
            required
          >
            <UFileUpload
              v-model="files"
              multiple
              layout="list"
              accept=".png,image/png"
              label="Choose PNG files"
              :file-image="false"
              :disabled="loading"
            >
              <template #file="{ file: selectedFile, index, removeFile }">
                <div class="grid w-full grid-cols-[auto_3rem_minmax(0,1fr)_minmax(0,1fr)] items-center gap-2 text-sm">
                  <UButton
                    type="button"
                    icon="lucide-x"
                    color="neutral"
                    variant="ghost"
                    :aria-label="`Remove ${selectedFile.name}`"
                    :disabled="loading"
                    @click.stop.prevent="removeFile(index)"
                  />
                  <img
                    v-if="uploads[index]?.image"
                    :src="`data:image/png;base64,${uploads[index].image}`"
                    :alt="`Preview of ${selectedFile.name}`"
                    class="size-12 object-contain"
                  >
                  <div
                    v-else
                    class="flex size-12 items-center justify-center"
                    aria-hidden="true"
                  >
                    <UIcon name="lucide-image" />
                  </div>
                  <div class="min-w-0">
                    <div class="break-all font-semibold">
                      {{ selectedFile.name }}
                    </div>
                    <div class="font-mono text-muted">
                      {{ uploads[index]?.hash }}
                    </div>
                    <div
                      v-if="uploads[index]?.error"
                      class="break-words text-error"
                    >
                      {{ uploads[index].error }}
                    </div>
                  </div>
                  <div class="min-w-0">
                    <div class="break-all">
                      {{ uploads[index]?.peerId || 'No peer available' }}
                    </div>
                    <div class="font-mono text-muted">
                      {{ uploads[index]?.peerHash || '-' }}
                    </div>
                  </div>
                </div>
              </template>
            </UFileUpload>
          </UFormField>
          <p
            v-if="missingPeer"
            class="text-sm text-error"
          >
            An assigned peer is unavailable. Remove and add the affected files when peers are available.
          </p>
          <p
            v-if="uploadError"
            class="text-sm text-error"
          >
            {{ uploadError }}
          </p>
          <div
            v-if="uploads.length"
            class="space-y-1"
          >
            <div class="text-sm">
              {{ sentCount }} / {{ uploads.length }} images sent
            </div>
            <UProgress
              :model-value="sentCount"
              :max="uploads.length"
            />
          </div>
          <UButton
            type="submit"
            :label="sentCount ? 'Continue upload' : 'Confirm upload'"
            :loading="loading"
            :disabled="!canSubmitMultiple"
          />
        </form>
        <form
          v-else
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
import { shortHash } from '~/composables/useHash'
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
const multiUpload = ref(false)
const files = ref<File[] | null>(null)
interface ImageUpload {
  file: File
  imageId: string
  hash: string
  peerId: string
  peerHash: string
  image: string
  error: string
  sent: boolean
}
const uploads = ref<ImageUpload[]>([])
const sentCount = computed(() => uploads.value.filter(upload => upload.sent).length)
const uploadError = ref('')
const preparing = ref(false)
let defaultImageId = ''
const preview = computed(() => image.value ? `data:image/png;base64,${image.value}` : '')
const canSubmit = computed(() => !!imageId.value.trim() && !!image.value && previewReady.value
  && props.peers.some(peer => peer.peerId === peerId.value))
const missingPeer = computed(() => uploads.value.some(upload => !upload.sent
  && !props.peers.some(peer => peer.peerId === upload.peerId)))
const canSubmitMultiple = computed(() => !loading.value && !preparing.value && !missingPeer.value
  && sentCount.value < uploads.value.length && uploads.value.every(upload => !!upload.image && !upload.error))

watch(files, async (selected, _previous, onCleanup) => {
  uploadError.value = ''
  const peers = props.peers
  const previous = [...uploads.value]
  uploads.value = (selected ?? []).map((selectedFile) => {
    const index = previous.findIndex(upload => upload.file === selectedFile)
    if (index !== -1) return previous.splice(index, 1)[0]!
    const peerId = peers[Math.floor(Math.random() * peers.length)]?.peerId ?? ''
    return {
      file: selectedFile,
      imageId: selectedFile.name,
      hash: shortHash(selectedFile.name),
      peerId,
      peerHash: peerId ? shortHash(peerId) : '',
      image: '',
      error: '',
      sent: false
    }
  })
  const pending = uploads.value.filter(upload => !upload.image && !upload.error)
  preparing.value = !!pending.length
  if (!pending.length) return

  let active = true
  onCleanup(() => {
    active = false
  })
  await Promise.all(pending.map(async (upload) => {
    try {
      const data = await readPngAsBase64(upload.file)
      await new Promise<void>((resolve, reject) => {
        const previewImage = new Image()
        previewImage.onload = () => resolve()
        previewImage.onerror = () => reject(new Error('Could not preview PNG file'))
        previewImage.src = `data:image/png;base64,${data}`
      })
      if (active) upload.image = data
    } catch (error) {
      if (active) upload.error = error instanceof Error ? error.message : String(error)
    }
  }))
  if (active) preparing.value = false
}, { flush: 'sync' })

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
  onCleanup(() => {
    active = false
  })
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
  files.value = null
  multiUpload.value = false
  open.value = true
}

async function submitMultiple() {
  if (!canSubmitMultiple.value) return
  loading.value = true
  uploadError.value = ''
  let currentUpload: ImageUpload | undefined
  try {
    for (const upload of uploads.value) {
      if (upload.sent) continue
      currentUpload = upload
      if (!props.peers.some(peer => peer.peerId === upload.peerId)) {
        throw new Error(`Peer ${upload.peerId} is no longer available`)
      }
      await putPeerImage(props.networkId, upload.peerId, upload.imageId, upload.image)
      upload.sent = true
    }
    useToast().add({
      title: 'Images accepted',
      description: 'The peers acknowledged the images; storage may still be in progress.',
      color: 'success'
    })
  } catch (error) {
    uploadError.value = `Failed to put ${currentUpload?.imageId ?? 'image'}: ${error instanceof Error ? error.message : String(error)}`
  } finally {
    loading.value = false
  }
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
