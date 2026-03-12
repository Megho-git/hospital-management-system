<template>
  <div>
    <PageHeader title="Medication Catalog" subtitle="Manage the standardized medication list used for prescriptions">
      <template #actions>
        <button @click="openCreate" class="btn-primary btn-sm">
          <Plus class="h-4 w-4" /> Add Medication
        </button>
      </template>
    </PageHeader>

    <SectionCard title="Catalog" class="mb-6">
      <div class="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div class="flex-1">
          <label class="label-text">Search</label>
          <input v-model="q" class="input-field" placeholder="Search by name, generic, strength, manufacturer..." />
        </div>
        <div class="w-full sm:w-48">
          <label class="label-text">Status</label>
          <select v-model="activeFilter" class="select-field">
            <option value="">All</option>
            <option value="1">Active</option>
            <option value="0">Inactive</option>
          </select>
        </div>
        <button @click="fetchMeds" class="btn-secondary">Refresh</button>
      </div>

      <SkeletonLoader v-if="loading" :rows="5" />
      <DataTable
        v-else
        :columns="columns"
        :data="medications"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No medications"
        emptyMessage="Add your first medication to start structured prescriptions."
      >
        <template #cell-name="{ row }">
          <div class="min-w-0">
            <p class="truncate font-medium text-slate-900">{{ row.name }}</p>
            <p v-if="row.generic_name" class="truncate text-xs text-slate-500">{{ row.generic_name }}</p>
          </div>
        </template>
        <template #cell-details="{ row }">
          <p class="text-sm text-slate-700">{{ [row.form, row.strength].filter(Boolean).join(' • ') || '--' }}</p>
          <p class="text-xs text-slate-500">{{ row.manufacturer || '' }}</p>
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

    <SectionCard :title="editing?.id ? 'Edit Medication' : 'Add Medication'" v-if="editing !== null" class="mb-6">
      <form @submit.prevent="submitForm" class="space-y-3">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
          <div class="sm:col-span-2">
            <label class="label-text">Name</label>
            <input v-model="form.name" class="input-field" placeholder="e.g. Paracetamol" />
          </div>
          <div class="sm:col-span-2">
            <label class="label-text">Generic name</label>
            <input v-model="form.generic_name" class="input-field" placeholder="e.g. Acetaminophen" />
          </div>
          <div>
            <label class="label-text">Form</label>
            <input v-model="form.form" class="input-field" placeholder="tablet / syrup / capsule" />
          </div>
          <div>
            <label class="label-text">Strength</label>
            <input v-model="form.strength" class="input-field" placeholder="e.g. 500mg" />
          </div>
          <div class="sm:col-span-2">
            <label class="label-text">Manufacturer</label>
            <input v-model="form.manufacturer" class="input-field" placeholder="e.g. Cipla" />
          </div>
          <div class="sm:col-span-2 flex items-center gap-2">
            <input id="is_active" v-model="form.is_active" type="checkbox" class="h-4 w-4 rounded border-slate-300" />
            <label for="is_active" class="text-sm text-slate-700">Active (available for prescribing)</label>
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
      title="Delete medication?"
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
const medications = ref([])
const page = ref(1)
const q = ref('')
const activeFilter = ref('')

const confirmOpen = ref(false)
const confirmText = ref('')
const deleteTarget = ref(null)

const editing = ref(null)
const form = reactive({ name: '', generic_name: '', form: '', strength: '', manufacturer: '', is_active: true })

const columns = [
  { key: 'name', label: 'Medication' },
  { key: 'details', label: 'Details' },
  { key: 'is_active', label: 'Status' },
  { key: 'actions', label: '' },
]

async function fetchMeds() {
  loading.value = true
  try {
    const params = {}
    if (q.value.trim()) params.q = q.value.trim()
    if (activeFilter.value !== '') params.active = parseInt(activeFilter.value)
    const { data } = await api.get('/admin/medications', { params })
    medications.value = data
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Failed to load medications')
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editing.value = null
  Object.assign(form, { name: '', generic_name: '', form: '', strength: '', manufacturer: '', is_active: true })
  // set sentinel non-null to show form
  editing.value = { id: null }
}

function openEdit(row) {
  editing.value = row
  Object.assign(form, {
    name: row.name || '',
    generic_name: row.generic_name || '',
    form: row.form || '',
    strength: row.strength || '',
    manufacturer: row.manufacturer || '',
    is_active: !!row.is_active,
  })
}

function cancelEdit() {
  editing.value = null
  Object.assign(form, { name: '', generic_name: '', form: '', strength: '', manufacturer: '', is_active: true })
}

async function submitForm() {
  try {
    if (!form.name.trim()) {
      toast.error('Name is required')
      return
    }
    if (editing.value?.id) {
      await api.put(`/admin/medications/${editing.value.id}`, form)
      toast.success('Medication updated')
    } else {
      await api.post('/admin/medications', form)
      toast.success('Medication added')
    }
    editing.value = null
    Object.assign(form, { name: '', generic_name: '', form: '', strength: '', manufacturer: '', is_active: true })
    fetchMeds()
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
    await api.delete(`/admin/medications/${deleteTarget.value.id}`)
    toast.success('Medication deleted')
    fetchMeds()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Delete failed')
  }
}

watch([q, activeFilter], () => {
  page.value = 1
})

onMounted(fetchMeds)
</script>

