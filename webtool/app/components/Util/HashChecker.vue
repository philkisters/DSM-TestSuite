<template>
  <div class="flex flex-col text-center justify-center w-2xl mx-auto">
    <h2 class="text-2xl font-bold my-2">Hash Checker</h2>
    <p class="text-center my-2 text-lg">
      Enter an ID to check if the hash matches.
    </p>
    <UInput type="text" placeholder="Enter ID" size="lg" v-model="id" />
    <div class="text-lg my-2">
      Resulting Hash:
    </div>
    <div class="p-2 font-mono bg-muted border border-muted rounded">
      <span class="text-primary">
        {{ hash.slice(0, 8) }}
      </span>
      <span>
        {{ hash.slice(8) }}
      </span>
    </div>
  </div>
</template>
<script setup lang="ts">
import { sha256 } from '@noble/hashes/sha2.js'
import { bytesToHex } from '@noble/hashes/utils.js'

const id = ref('')

const hash = computed(() => {
  return bytesToHex(sha256(new TextEncoder().encode(id.value)))
})

</script>