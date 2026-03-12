<template>
  <div>
    <PageHeader title="Treatment History" subtitle="View your past consultations and prescriptions" />

    <SkeletonLoader v-if="loading" :rows="4" />
    <DataTable
      v-else
      :columns="columns"
      :data="treatments"
      :page="page"
      @update:page="page = $event"
      searchable
      :searchQuery="search"
      @update:searchQuery="search = $event"
      searchPlaceholder="Search by doctor, diagnosis..."
      emptyTitle="No treatment history"
      emptyMessage="Your treatment records will appear here after completed appointments."
    >
      <template #cell-visit_date="{ row }">
        <span class="font-medium text-slate-900">{{ formatDate(row.visit_date) }}</span>
      </template>
      <template #cell-doctor_name="{ row }">
        <span>Dr. {{ row.doctor_name }}</span>
      </template>
      <template #cell-diagnosis="{ row }">
        <span class="line-clamp-2 max-w-xs">{{ row.diagnosis || '--' }}</span>
      </template>
      <template #cell-prescription="{ row }">
        <span class="line-clamp-2 max-w-xs">{{ row.prescription || '--' }}</span>
      </template>
      <template #cell-medicines="{ row }">
        <div v-if="row.prescribed_medicines?.length" class="space-y-1">
          <div v-for="pm in row.prescribed_medicines" :key="pm.id || pm.medication_id" class="text-sm">
            <span class="font-medium text-slate-900">{{ pm.name }}</span>
            <span class="text-slate-500"> {{ pm.strength || '' }}</span>
            <span class="text-slate-500"> — {{ [pm.dose, pm.frequency, pm.duration].filter(Boolean).join(' • ') }}</span>
            <span v-if="pm.instructions" class="block text-xs text-slate-500">{{ pm.instructions }}</span>
          </div>
        </div>
        <div v-else-if="row.medicines" class="flex flex-wrap gap-1">
          <span
            v-for="med in row.medicines.split(',')"
            :key="med"
            class="inline-block rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700"
          >
            {{ med.trim() }}
          </span>
        </div>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-visit_type="{ row }">
        <StatusChip v-if="row.visit_type" :status="row.visit_type.toLowerCase()" :label="row.visit_type" />
        <span v-else class="text-slate-400">--</span>
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
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const loading = ref(true)
const allTreatments = ref([])
const page = ref(1)
const search = ref('')

const columns = [
  { key: 'visit_date', label: 'Date' },
  { key: 'doctor_name', label: 'Doctor' },
  { key: 'diagnosis', label: 'Diagnosis' },
  { key: 'prescription', label: 'Prescription' },
  { key: 'medicines', label: 'Medicines' },
  { key: 'visit_type', label: 'Type' },
]

const treatments = computed(() => {
  if (!search.value.trim()) return allTreatments.value
  const q = search.value.toLowerCase()
  return allTreatments.value.filter(t =>
    (t.doctor_name || '').toLowerCase().includes(q) ||
    (t.diagnosis || '').toLowerCase().includes(q) ||
    (t.medicines || '').toLowerCase().includes(q)
  )
})

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

onMounted(async () => {
  const { data } = await api.get('/patient/history')
  allTreatments.value = data
  loading.value = false
})
</script>
