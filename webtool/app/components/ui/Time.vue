<template>
  <div>
    <span v-if="showDate">
      {{ timestamp.toLocaleDateString() }}
    </span>
    <span v-if="showDate && showTime">
      @
    </span>
    <span v-if="showTime">
      {{ timestamp.toLocaleTimeString() }} 
    </span>
  </div>
</template>

<script setup lang="ts">

const { timestamp, showDate = true, showTime = true } = defineProps<{
  timestamp: Date
  showDate?: boolean
  showTime?: boolean
}>()
</script>