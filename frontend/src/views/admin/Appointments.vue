<template>
  <div>
    <PageHeader title="All Appointments" subtitle="View and filter all hospital appointments" />

    <DataTable
      :columns="columns"
      :data="filteredAppointments"
      :page="page"
      @update:page="page = $event"
      emptyTitle="No appointments found"
    >
      <template #toolbar>
        <select v-model="statusFilter" @change="fetch" class="select-field w-auto">
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="confirmed">Confirmed</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        <option value="no_show">No-show</option>
        </select>
      </template>
      <template #cell-id="{ row }">
        <span class="font-mono text-xs text-slate-500">#{{ row.id }}</span>
      </template>
      <template #cell-patient_name="{ row }">
        <span class="font-medium text-slate-900">{{ row.patient_name }}</span>
      </template>
      <template #cell-doctor_name="{ row }">
        <span>Dr. {{ row.doctor_name }}</span>
        <span class="block text-xs text-slate-400">{{ row.specialization }}</span>
      </template>
      <template #cell-date="{ row }">
        <span>{{ formatDate(row.date) }}</span>
        <span class="block text-xs text-slate-400">{{ row.time_slot }}</span>
      </template>
      <template #cell-status="{ row }">
        <StatusChip :status="row.status" :label="row.status" />
      </template>
      <template #cell-reason="{ row }">
        <span class="line-clamp-1 max-w-xs text-sm text-slate-500">{{ row.reason || '--' }}</span>
      </template>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import DataTable from '@/components/DataTable.vue'
import StatusChip from '@/components/StatusChip.vue'

const appointments = ref([])
const statusFilter = ref('')
const page = ref(1)

const columns = [
  { key: 'id', label: '#' },
  { key: 'patient_name', label: 'Patient' },
  { key: 'doctor_name', label: 'Doctor' },
  { key: 'date', label: 'Schedule' },
  { key: 'status', label: 'Status' },
  { key: 'reason', label: 'Reason' },
]

const filteredAppointments = computed(() => appointments.value)

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function fetch() {
  const params = {}
  if (statusFilter.value) params.status = statusFilter.value
  const { data } = await api.get('/admin/appointments', { params })
  appointments.value = data
  page.value = 1
}

onMounted(fetch)
</script>
