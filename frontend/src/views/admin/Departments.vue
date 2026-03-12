<template>
  <div>
    <PageHeader title="Departments" subtitle="Create and manage departments" />

    <div class="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Department List">
        <SkeletonLoader v-if="loading" :rows="5" />
        <DataTable
          v-else
          :columns="columns"
          :data="departments"
          :page="page"
          @update:page="page = $event"
          emptyTitle="No departments"
          emptyMessage="Create your first department to organize doctors and services."
        >
          <template #cell-name="{ row }">
            <p class="font-medium text-slate-900">{{ row.name }}</p>
            <p class="text-xs text-slate-500">{{ row.description || '' }}</p>
          </template>
          <template #cell-actions="{ row }">
            <div class="flex gap-1 justify-end">
              <button class="btn-ghost btn-sm text-primary-600" @click="edit(row)">Edit</button>
              <button class="btn-ghost btn-sm text-danger-600" @click="confirmDelete(row)">Delete</button>
            </div>
          </template>
        </DataTable>
      </SectionCard>

      <SectionCard :title="editing?.id ? 'Edit Department' : 'Add Department'">
        <form @submit.prevent="save" class="space-y-4">
          <div>
            <label class="label-text">Name</label>
            <input v-model="form.name" class="input-field" placeholder="e.g. Cardiology" />
          </div>
          <div>
            <label class="label-text">Description</label>
            <textarea v-model="form.description" class="input-field" rows="4" placeholder="Optional description..." />
          </div>
          <div class="flex gap-2">
            <button type="submit" class="btn-primary">{{ editing?.id ? 'Save changes' : 'Create department' }}</button>
            <button type="button" class="btn-secondary" @click="reset">Clear</button>
          </div>
        </form>
      </SectionCard>
    </div>

    <ConfirmDialog
      v-model="confirmOpen"
      title="Delete department?"
      :message="confirmText"
      confirmText="Delete"
      variant="danger"
      @confirm="doDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const toast = useToast()
const loading = ref(true)
const departments = ref([])
const page = ref(1)

const editing = ref(null)
const form = reactive({ name: '', description: '' })

const confirmOpen = ref(false)
const confirmText = ref('')
const deleteTarget = ref(null)

const columns = [
  { key: 'name', label: 'Department' },
  { key: 'actions', label: '', align: 'right' },
]

async function fetchDepts() {
  loading.value = true
  const { data } = await api.get('/admin/departments')
  departments.value = data || []
  loading.value = false
}

function edit(row) {
  editing.value = row
  form.name = row.name
  form.description = row.description || ''
}

function reset() {
  editing.value = null
  form.name = ''
  form.description = ''
}

async function save() {
  try {
    if (!form.name.trim()) {
      toast.error('Name is required')
      return
    }
    if (editing.value?.id) {
      await api.put(`/admin/departments/${editing.value.id}`, form)
      toast.success('Department updated')
    } else {
      await api.post('/admin/departments', form)
      toast.success('Department created')
    }
    reset()
    fetchDepts()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Save failed')
  }
}

function confirmDelete(row) {
  deleteTarget.value = row
  confirmText.value = `Delete ${row.name}?`
  confirmOpen.value = true
}

async function doDelete() {
  try {
    await api.delete(`/admin/departments/${deleteTarget.value.id}`)
    toast.success('Department deleted')
    fetchDepts()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Delete failed')
  }
}

onMounted(fetchDepts)
</script>

