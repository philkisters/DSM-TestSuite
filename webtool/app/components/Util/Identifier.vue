<template>
  <div class="min-w-0">
    <div class="font-mono break-all">
      {{ id }}
    </div>
    <div class="font-mono text-muted text-xs" :title="hashId(id)">
      {{ shortHash(id) }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { hashId, shortHash } from '~/composables/useHash'

defineProps<{ id: string }>()
</script>
