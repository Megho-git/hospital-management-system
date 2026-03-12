<template>
  <div>
    <PageHeader title="Vitals History" subtitle="Track recorded vitals from your visits">
      <template #actions>
        <div class="text-right">
          <p class="text-xs text-slate-500">BP trend (last 5)</p>
          <p class="text-sm font-semibold text-slate-900">{{ bpTrend }}</p>
        </div>
        <div class="text-right">
          <p class="text-xs text-slate-500">Pulse trend (last 5)</p>
          <p class="text-sm font-semibold text-slate-900">{{ pulseTrend }}</p>
        </div>
      </template>
    </PageHeader>

    <SkeletonLoader v-if="loading" :rows="5" />
    <DataTable
      v-else
      :columns="columns"
      :data="vitals"
      :page="page"
      @update:page="page = $event"
      emptyTitle="No vitals recorded"
      emptyMessage="Vitals will appear here after your doctor records them during a visit."
    >
      <template #cell-recorded_at="{ row }">
        <span class="font-medium text-slate-900">{{ formatDateTime(row.recorded_at) }}</span>
        <span class="block text-xs text-slate-400">Dr. {{ row.doctor_name || '--' }}</span>
      </template>
      <template #cell-bp="{ row }">
        <span v-if="row.blood_pressure_systolic && row.blood_pressure_diastolic" class="font-medium text-slate-900">
          {{ row.blood_pressure_systolic }}/{{ row.blood_pressure_diastolic }}
        </span>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-temp="{ row }">
        <span v-if="row.temperature != null" class="text-slate-700">{{ row.temperature }}°C</span>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-pulse="{ row }">
        <span v-if="row.pulse_rate != null" class="text-slate-700">{{ row.pulse_rate }}</span>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-spo2="{ row }">
        <span v-if="row.spo2 != null" class="text-slate-700">{{ row.spo2 }}%</span>
        <span v-else class="text-slate-400">--</span>
      </template>
      <template #cell-rr="{ row }">
        <span v-if="row.respiratory_rate != null" class="text-slate-700">{{ row.respiratory_rate }}</span>
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
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const loading = ref(true)
const all = ref([])
const page = ref(1)

const columns = [
  { key: 'recorded_at', label: 'Recorded' },
  { key: 'bp', label: 'BP' },
  { key: 'temp', label: 'Temp' },
  { key: 'pulse', label: 'Pulse' },
  { key: 'spo2', label: 'SpO₂' },
  { key: 'rr', label: 'Resp' },
]

const vitals = computed(() => all.value)

function formatDateTime(iso) {
  if (!iso) return '--'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

function simpleTrend(values) {
  const nums = values.filter(v => typeof v === 'number' && !Number.isNaN(v))
  if (nums.length < 2) return '—'
  const first = nums[0]
  const last = nums[nums.length - 1]
  if (last > first) return `↑ ${first} → ${last}`
  if (last < first) return `↓ ${first} → ${last}`
  return `→ ${first} → ${last}`
}

const bpTrend = computed(() => {
  const last5 = all.value.slice(0, 5).filter(v => v.blood_pressure_systolic && v.blood_pressure_diastolic)
  if (!last5.length) return '—'
  const first = `${last5[last5.length - 1].blood_pressure_systolic}/${last5[last5.length - 1].blood_pressure_diastolic}`
  const last = `${last5[0].blood_pressure_systolic}/${last5[0].blood_pressure_diastolic}`
  return first === last ? `→ ${first}` : `${first} → ${last}`
})

const pulseTrend = computed(() => simpleTrend(all.value.slice(0, 5).map(v => v.pulse_rate)))

onMounted(async () => {
  const { data } = await api.get('/patient/vitals')
  all.value = data || []
  loading.value = false
})
</script>

