<template>
  <UBadge :icon="statusIcon" size="lg" :color="statusColor" variant="solid">{{ props.status }}</UBadge>
</template>
<script setup lang="ts">
const props = defineProps<{
  status: "passed" | "failed"
  size?: "lg" |"xl"
}>()

const statusColor = computed(() => {
  return props.status === "passed" ? "success" : "error"
})

const statusIcon = computed(() => {
  return props.status === "passed" ? "lucide-check" : "lucide-x"
})
</script>