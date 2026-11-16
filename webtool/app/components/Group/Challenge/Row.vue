<template>
  <div class="flex gap-2">
    <div
      class="flex items-center gap-1"
      :aria-label="`${first} first places`"
    >
      <UIcon
        name="lucide-trophy"
        class="size-5 text-amber-500"
        aria-hidden="true"
      />
      {{ first }}
    </div>
    <div
      class="flex items-center gap-1"
      :aria-label="`${second} second places`"
    >
      <UIcon
        name="lucide-star"
        class="size-5 text-gray-400"
        aria-hidden="true"
      />
      {{ second }}
    </div>
    <div
      class="flex items-center gap-1"
      :aria-label="`${third} third places`"
    >
      <UIcon
        name="lucide-star"
        class="size-5 text-amber-700"
        aria-hidden="true"
      />
      {{ third }}
    </div>
  </div>
</template>

<script setup lang="ts">

const { first = 0, second = 0, third = 0 } = defineProps<{
  first?: number
  second?: number
  third?: number
}>()
</script>