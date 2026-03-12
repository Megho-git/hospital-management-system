<template>
  <div>
    <PageHeader title="Lab Results" subtitle="View investigations ordered during your visits" />

    <SkeletonLoader v-if="loading" :rows="5" />
    <DataTable
      v-else
      :columns="columns"
      :data="rows"
      :page="page"
      @update:page="page = $event"
      searchable
      :searchQuery="search"
      @update:searchQuery="search = $event"
      searchPlaceholder="Search test name or category..."
      emptyTitle="No lab results"
      emptyMessage="Lab orders and results will appear here."
    >
      <template #cell-test="{ row }">
        <p class="font-medium text-slate-900">{{ row.lab_test?.name || '--' }}</p>
        <p class="text-xs text-slate-500">{{ row.lab_test?.category || '' }}</p>
      </template>
      <template #cell-ordered_at="{ row }">
        <span class="text-sm text-slate-700">{{ formatDate(row.ordered_at) }}</span>
        <span class="block text-xs text-slate-400">Dr. {{ row.doctor_name || '--' }}</span>
      </template>
      <template #cell-status="{ row }">
        <StatusChip :status="row.status" :label="row.status" />
      </template>
      <template #cell-result="{ row }">
        <div v-if="row.result_value" class="text-sm">
          <span class="font-semibold text-slate-900">{{ row.result_value }}</span>
          <span v-if="row.lab_test?.unit" class="text-slate-500"> {{ row.lab_test.unit }}</span>
          <span v-if="flag(row) === 'abnormal'" class="ml-2 rounded-full bg-danger-50 px-2 py-0.5 text-xs font-semibold text-danger-700 ring-1 ring-danger-500/20">Abnormal</span>
          <span v-else-if="flag(row) === 'normal'" class="ml-2 rounded-full bg-success-50 px-2 py-0.5 text-xs font-semibold text-success-700 ring-1 ring-success-500/20">Normal</span>
        </div>
        <span v-else class="text-slate-400">--</span>
        <p v-if="row.lab_test?.normal_range" class="text-xs text-slate-500">Range: {{ row.lab_test.normal_range }}</p>
        <div class="mt-1 flex gap-2">
          <button v-if="row.has_result_file" @click="downloadFile(row.id)" class="text-xs font-medium text-primary-600 hover:text-primary-700">Download Report</button>
          <button @click="showHistory(row)" class="text-xs font-medium text-slate-500 hover:text-slate-700">History</button>
        </div>
      </template>
    </DataTable>

    <!-- Status history modal -->
    <div v-if="historyModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="historyModal = null">
      <div class="card w-full max-w-md max-h-[70vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-3">Status History — {{ historyModal.lab_test?.name }}</h3>
        <div v-if="historyEntries.length" class="space-y-2">
          <div v-for="h in historyEntries" :key="h.id" class="rounded-lg border border-slate-200 p-2 text-sm">
            <div class="flex justify-between">
              <span><span class="text-slate-400">{{ h.old_status || '—' }}</span> → <span class="font-medium">{{ h.new_status }}</span></span>
              <span class="text-xs text-slate-400">{{ formatDate(h.created_at) }}</span>
            </div>
            <p v-if="h.notes" class="mt-1 text-xs text-slate-500">{{ h.notes }}</p>
          </div>
        </div>
        <p v-else class="text-sm text-slate-400 py-4 text-center">No history entries yet.</p>
        <button class="btn mt-3" @click="historyModal = null">Close</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import StatusChip from '@/components/StatusChip.vue'

const loading = ref(true)
const all = ref([])
const page = ref(1)
const search = ref('')
const historyModal = ref(null)
const historyEntries = ref([])

const columns = [
  { key: 'test', label: 'Test' },
  { key: 'ordered_at', label: 'Ordered' },
  { key: 'status', label: 'Status' },
  { key: 'result', label: 'Result' },
]

const rows = computed(() => {
  if (!search.value.trim()) return all.value
  const q = search.value.toLowerCase()
  return all.value.filter(r =>
    (r.lab_test?.name || '').toLowerCase().includes(q) ||
    (r.lab_test?.category || '').toLowerCase().includes(q)
  )
})

function formatDate(iso) {
  if (!iso) return '--'
  return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function flag(row) {
  const range = row.lab_test?.normal_range || ''
  const val = row.result_value
  if (!range || val == null) return null
  const m = String(range).match(/^\s*(-?\d+(\.\d+)?)\s*-\s*(-?\d+(\.\d+)?)\s*$/)
  const n = Number(val)
  if (!m || Number.isNaN(n)) return null
  const lo = Number(m[1])
  const hi = Number(m[3])
  if (n < lo || n > hi) return 'abnormal'
  return 'normal'
}

function downloadFile(orderId) {
  window.open(`/api/v2/labs/orders/${orderId}/result-file`, '_blank')
}

async function showHistory(row) {
  historyModal.value = row
  try {
    const { data } = await api.get(`/v2/labs/orders/${row.id}/history`)
    historyEntries.value = data
  } catch {
    historyEntries.value = []
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get('/v2/labs/orders')
    all.value = data || []
  } catch {
    const { data } = await api.get('/patient/lab-results')
    all.value = data || []
  }
  loading.value = false
})
</script>

