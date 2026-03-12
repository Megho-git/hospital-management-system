<template>
  <div>
    <PageHeader title="Patients" subtitle="View and manage registered patients" />

    <DataTable
      :columns="columns"
      :data="filteredPatients"
      :page="page"
      @update:page="page = $event"
      searchable
      :searchQuery="search"
      @update:searchQuery="onSearch"
      searchPlaceholder="Search by name, email, phone, or ID..."
      emptyTitle="No patients found"
    >
      <template #cell-username="{ row }">
        <div class="flex items-center gap-3">
          <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-success-50 text-xs font-bold text-success-600">
            {{ row.username.charAt(0).toUpperCase() }}
          </div>
          <div>
            <p class="font-medium text-slate-900">{{ row.username }}</p>
            <p class="text-xs text-slate-500">{{ row.email }}</p>
          </div>
        </div>
      </template>
      <template #cell-blood_group="{ row }">
        <span v-if="row.blood_group" class="inline-block rounded-full bg-danger-50 px-2 py-0.5 text-xs font-semibold text-danger-600">
          {{ row.blood_group }}
        </span>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-insurance_provider="{ row }">
        <span class="text-sm text-slate-700">{{ row.insurance_provider || '--' }}</span>
      </template>
      <template #cell-allergies_count="{ row }">
        <span class="text-sm text-slate-700">{{ countAllergies(row.allergies) }}</span>
      </template>
      <template #cell-status="{ row }">
        <StatusChip :status="row.is_active ? 'active' : 'blocked'" :label="row.is_active ? 'Active' : 'Blocked'" />
      </template>
      <template #cell-actions="{ row }">
        <button
          @click="toggleUser(row)"
          :class="row.is_active ? 'text-danger-600' : 'text-success-600'"
          class="btn-ghost btn-sm"
        >
          {{ row.is_active ? 'Block' : 'Unblock' }}
        </button>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import DataTable from '@/components/DataTable.vue'
import StatusChip from '@/components/StatusChip.vue'

const toast = useToast()
const patients = ref([])
const search = ref('')
const page = ref(1)

const columns = [
  { key: 'username', label: 'Patient' },
  { key: 'phone', label: 'Phone' },
  { key: 'gender', label: 'Gender' },
  { key: 'blood_group', label: 'Blood Group' },
  { key: 'insurance_provider', label: 'Insurance' },
  { key: 'allergies_count', label: 'Allergies' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

const filteredPatients = computed(() => {
  if (!search.value.trim()) return patients.value
  const q = search.value.toLowerCase()
  return patients.value.filter(p =>
    p.username.toLowerCase().includes(q) ||
    (p.email || '').toLowerCase().includes(q) ||
    (p.phone || '').toLowerCase().includes(q) ||
    String(p.id).includes(q)
  )
})

function countAllergies(allergies) {
  if (!allergies) return 0
  return String(allergies)
    .split(',')
    .map(x => x.trim())
    .filter(Boolean).length
}

function onSearch(val) {
  search.value = val
  page.value = 1
}

async function toggleUser(p) {
  await api.put(`/admin/users/${p.user_id}/toggle`)
  toast.info(`User ${p.is_active ? 'blocked' : 'activated'}`)
  fetchPatients()
}

async function fetchPatients() {
  const { data } = await api.get('/admin/patients')
  patients.value = data
}

onMounted(fetchPatients)
</script>
