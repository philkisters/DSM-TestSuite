<template>
  <UModal :open="true" :dismissible="false" title="Select your Group" :close="false">
    <template #body>
      <div class="grid grid-cols-3 gap-4" v-if="!groupCreation">
        <GroupSelectionItem v-for="group in groups" :key="group.id" :group="group" @click="selectGroup(group.id)" />
      </div>
      <div v-else>
        <UFormField label="Group Name">
          <UInput v-model="newGroup.name"/>
        </UFormField>
        <UFormField label="VM IP">
          <UInput v-model="newGroup.vmIp"/>
        </UFormField>
      </div>
    </template>
    <template #footer>
      <UButton
        size="lg"
        color="primary"
        variant="outline"
        icon="lucide-plus"
        @click="startGroupCreation"
        v-if="false"
      >
        Create New Group
      </UButton>
      <UButton
        size="lg"
        color="primary"
        variant="outline"
        icon="lucide-check"
        @click="createGroup"
        v-if="groupCreation"
      >
        Create Group
      </UButton>
      <UButton
        size="lg"
        color="warning"
        variant="outline"
        icon="lucide-x"
        @click="groupCreation = false"
        v-if="groupCreation"
      >
        Cancel
      </UButton>
    </template>
  </UModal>
</template>
<script setup lang="ts">
const groupStore = useGroupStore()

const groups = computed(() => groupStore.groups)
// disabled for now. Group creation is temporarily turned off.
const groupCreation = ref(false)

const newGroup = ref({
  name: '',
  vmIp: ''
})

function selectGroup(groupId: number) {
  groupStore.setActiveGroup(groupId)
}

function startGroupCreation() {
  groupCreation.value = true
  newGroup.value = {
    name: '',
    vmIp: ''
  }
}

function createGroup() {
  return
  groupStore.createGroup(newGroup.value)
  groupCreation.value = false
}
</script>