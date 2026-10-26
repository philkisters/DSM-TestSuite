<template>
  <div class="flex flex-grow p-4">
    <div class="flex flex-col text-center justify-start w-full">
      <h1 class="text-center text-4xl font-bold my-4">Utilities</h1>
      <p class="text-center text-2xl">
        Here you will find all the currently available utilities. The first is a small hash checker, to see if we have the same hash for a given ID.
      </p>
      <USeparator class="my-4" />
      <div class="flex flex-col text-center justify-start w-full">
        <UtilHashChecker />
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
</script>