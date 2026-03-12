<template>
  <div>
    <PageHeader title="Analytics" subtitle="Operational insights across appointments and departments" />

    <SkeletonLoader v-if="loading" :rows="6" />
    <template v-else>
      <div class="mb-6 grid gap-6 lg:grid-cols-2">
        <SectionCard title="Appointment load (last 30 days)">
          <div class="h-[280px]">
            <canvas ref="loadCanvas" />
          </div>
        </SectionCard>
        <SectionCard title="Patient inflow (last 30 days)">
          <div class="h-[280px]">
            <canvas ref="inflowCanvas" />
          </div>
        </SectionCard>
      </div>

      <div class="mb-6 grid gap-6 lg:grid-cols-2">
        <SectionCard title="Department utilization">
          <div class="h-[320px]">
            <canvas ref="deptCanvas" />
          </div>
        </SectionCard>
        <SectionCard title="Top doctors (by appointments)">
          <DataTable :columns="docCols" :data="doctorItems" emptyTitle="No data" emptyMessage="No appointments in selected window." />
        </SectionCard>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import DataTable from '@/components/DataTable.vue'
import Chart from 'chart.js/auto'
import 'chartjs-adapter-date-fns'

const loading = ref(true)
const loadCanvas = ref(null)
const inflowCanvas = ref(null)
const deptCanvas = ref(null)

let loadChart = null
let inflowChart = null
let deptChart = null

const doctorItems = ref([])
const docCols = [
  { key: 'doctor_name', label: 'Doctor' },
  { key: 'department', label: 'Department' },
  { key: 'total', label: 'Total' },
  { key: 'completed', label: 'Completed' },
  { key: 'no_show', label: 'No-show' },
  { key: 'cancellation_rate', label: 'Cancel %' },
]

function destroyCharts() {
  if (loadChart) loadChart.destroy()
  if (inflowChart) inflowChart.destroy()
  if (deptChart) deptChart.destroy()
  loadChart = inflowChart = deptChart = null
}

function render({ loadSeries, inflowSeries, deptItems }) {
  destroyCharts()

  loadChart = new Chart(loadCanvas.value, {
    type: 'line',
    data: {
      datasets: [{
        label: 'Appointments',
        data: loadSeries.map(p => ({ x: p.date, y: p.count })),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      scales: { x: { type: 'time', time: { unit: 'day' } } },
    },
  })

  inflowChart = new Chart(inflowCanvas.value, {
    type: 'line',
    data: {
      datasets: [{
        label: 'New patients',
        data: inflowSeries.map(p => ({ x: p.date, y: p.count })),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      parsing: false,
      scales: { x: { type: 'time', time: { unit: 'day' } } },
    },
  })

  deptChart = new Chart(deptCanvas.value, {
    type: 'bar',
    data: {
      labels: deptItems.map(d => d.department),
      datasets: [{
        label: 'Appointments',
        data: deptItems.map(d => d.appointments),
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
    },
  })
}

onMounted(async () => {
  const [loadRes, deptRes, docRes, inflowRes] = await Promise.all([
    api.get('/v2/analytics/appointments/load', { params: { days: 30 } }),
    api.get('/v2/analytics/departments/utilization', { params: { days: 30 } }),
    api.get('/v2/analytics/doctors/performance', { params: { days: 30 } }),
    api.get('/v2/analytics/patients/inflow', { params: { days: 30 } }),
  ])
  doctorItems.value = docRes.data.items || []
  render({
    loadSeries: loadRes.data.series || [],
    inflowSeries: inflowRes.data.series || [],
    deptItems: deptRes.data.items || [],
  })
  loading.value = false
})

onBeforeUnmount(() => destroyCharts())
</script>

