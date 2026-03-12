<template>
  <div>
    <PageHeader title="Lab Tests" subtitle="Manage the investigations catalog used for lab orders">
      <template #actions>
        <button @click="openCreate" class="btn-primary btn-sm">
          <Plus class="h-4 w-4" /> Add Lab Test
        </button>
      </template>
    </PageHeader>

    <SectionCard title="Catalog" class="mb-6">
      <div class="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div class="flex-1">
          <label class="label-text">Search</label>
          <input v-model="q" class="input-field" placeholder="Search by name, category, unit, normal range..." />
        </div>
        <div class="w-full sm:w-48">
          <label class="label-text">Status</label>
          <select v-model="activeFilter" class="select-field">
            <option value="">All</option>
            <option value="1">Active</option>
            <option value="0">Inactive</option>
          </select>
        </div>
        <button @click="fetchTests" class="btn-secondary">Refresh</button>
      </div>

      <SkeletonLoader v-if="loading" :rows="5" />
      <DataTable
        v-else
        :columns="columns"
        :data="tests"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No lab tests"
        emptyMessage="Add your first lab test to start ordering investigations."
      >
        <template #cell-name="{ row }">
          <div class="min-w-0">
            <p class="truncate font-medium text-slate-900">{{ row.name }}</p>
            <p class="truncate text-xs text-slate-500">{{ row.category || 'Uncategorized' }}</p>
          </div>
        </template>
        <template #cell-range="{ row }">
          <p class="text-sm text-slate-700">{{ row.normal_range || '--' }}</p>
          <p class="text-xs text-slate-500">{{ row.unit || '' }}</p>
        </template>
        <template #cell-is_active="{ row }">
          <StatusChip :status="row.is_active ? 'active' : 'blocked'" :label="row.is_active ? 'Active' : 'Inactive'" />
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-1">
            <button class="btn-ghost btn-sm text-primary-600" @click="openEdit(row)">Edit</button>
            <button class="btn-ghost btn-sm text-danger-600" @click="confirmDelete(row)">Delete</button>
          </div>
        </template>
      </DataTable>
    </SectionCard>

    <SectionCard :title="editing?.id ? 'Edit Lab Test' : 'Add Lab Test'" v-if="editing !== null" class="mb-6">
      <form @submit.prevent="submitForm" class="space-y-3">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label class="label-text">Name</label>
            <input v-model="form.name" class="input-field" placeholder="e.g. HbA1c" />
          </div>
          <div>
            <label class="label-text">Category</label>
            <input v-model="form.category" class="input-field" placeholder="e.g. Biochemistry" />
          </div>
          <div>
            <label class="label-text">Unit</label>
            <input v-model="form.unit" class="input-field" placeholder="e.g. mg/dL" />
          </div>
          <div class="sm:col-span-2">
            <label class="label-text">Normal Range</label>
            <input v-model="form.normal_range" class="input-field" placeholder="e.g. 70-110" />
          </div>
          <div class="sm:col-span-2">
            <label class="label-text">Description</label>
            <textarea v-model="form.description" class="input-field" rows="3" placeholder="What this test measures..." />
          </div>
          <div class="sm:col-span-2 flex items-center gap-2">
            <input id="is_active" v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            <label for="is_active" class="text-sm text-slate-700">Active (available for ordering)</label>
          </div>
        </div>
        <div class="flex gap-2 pt-2">
          <button type="submit" class="btn-primary">Save</button>
          <button type="button" class="btn-secondary" @click="cancelEdit">Cancel</button>
        </div>
      </form>
    </SectionCard>

    <ConfirmDialog
      v-model="confirmOpen"
      title="Delete lab test?"
      :message="confirmText"
      confirmText="Delete"
      variant="danger"
      @confirm="doDelete"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import StatusChip from '@/components/StatusChip.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus } from 'lucide-vue-next'

const toast = useToast()
const loading = ref(true)
const tests = ref([])
const page = ref(1)
const q = ref('')
const activeFilter = ref('')

const confirmOpen = ref(false)
const confirmText = ref('')
const deleteTarget = ref(null)

const editing = ref(null)
const form = reactive({ name: '', description: '', normal_range: '', unit: '', category: '', is_active: true })

const columns = [
  { key: 'name', label: 'Test' },
  { key: 'range', label: 'Range' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' },
]

async function fetchTests() {
  loading.value = true
  try {
    const params = {}
    if (q.value.trim()) params.q = q.value.trim()
    if (activeFilter.value !== '') params.active = parseInt(activeFilter.value)
    const { data } = await api.get('/admin/lab-tests', { params })
    tests.value = data
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Failed to load lab tests')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = { id: null }
  Object.assign(form, { name: '', description: '', normal_range: '', unit: '', category: '', is_active: true })
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    name: row.name || '',
    description: row.description || '',
    normal_range: row.normal_range || '',
    unit: row.unit || '',
    category: row.category || '',
    is_active: !!row.is_active,
  })
}

function cancelEdit() {
  editing.value = null
  Object.assign(form, { name: '', description: '', normal_range: '', unit: '', category: '', is_active: true })
}

async function submitForm() {
  try {
    if (!form.name.trim()) {
      toast.error('Name is required')
      return
    }
    if (editing.value?.id) {
      await api.put(`/admin/lab-tests/${editing.value.id}`, form)
      toast.success('Lab test updated')
    } else {
      await api.post('/admin/lab-tests', form)
      toast.success('Lab test added')
    }
    cancelEdit()
    fetchTests()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Save failed')
  }
}

function confirmDelete(row) {
  deleteTarget.value = row
  confirmText.value = `Delete ${row.name}? This cannot be undone.`
  confirmOpen.value = true
}

async function doDelete() {
  try {
    await api.delete(`/admin/lab-tests/${deleteTarget.value.id}`)
    toast.success('Lab test deleted')
    fetchTests()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Delete failed')
  }
}

watch([q, activeFilter], () => { page.value = 1 })
onMounted(fetchTests)
</script>

