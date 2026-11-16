<template>
  Hash:
  <span class="font-mono text-primary">{{ hash }}</span>
</template>

<script setup lang="ts">
import { shortHash } from '~/composables/useHash'

const props = defineProps<{ value: string }>()
const hash = computed(() => props.value ? shortHash(props.value) : '-')
</script>
