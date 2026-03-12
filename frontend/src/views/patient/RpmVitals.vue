<template>
  <div>
    <PageHeader title="Health Trends (RPM)" subtitle="Upload vitals and track trends over time" />

    <SectionCard title="Add reading" class="mb-6">
      <form class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3" @submit.prevent="submit">
        <div>
          <label class="label-text">BP Systolic</label>
          <input v-model.number="form.blood_pressure_systolic" type="number" class="input-field" placeholder="e.g. 120" />
        </div>
        <div>
          <label class="label-text">BP Diastolic</label>
          <input v-model.number="form.blood_pressure_diastolic" type="number" class="input-field" placeholder="e.g. 80" />
        </div>
        <div>
          <label class="label-text">Heart rate</label>
          <input v-model.number="form.heart_rate" type="number" class="input-field" placeholder="bpm" />
        </div>
        <div>
          <label class="label-text">Glucose</label>
          <input v-model.number="form.glucose_mg_dl" type="number" step="0.1" class="input-field" placeholder="mg/dL" />
        </div>
        <div>
          <label class="label-text">SpO₂</label>
          <input v-model.number="form.spo2" type="number" class="input-field" placeholder="%" />
        </div>
        <div>
          <label class="label-text">Temperature</label>
          <input v-model.number="form.temperature_c" type="number" step="0.1" class="input-field" placeholder="°C" />
        </div>
        <div>
          <label class="label-text">Weight</label>
          <input v-model.number="form.weight_kg" type="number" step="0.1" class="input-field" placeholder="kg" />
        </div>
        <div class="lg:col-span-2">
          <label class="label-text">Notes</label>
          <input v-model="form.notes" class="input-field" placeholder="Optional" />
        </div>
        <div class="sm:col-span-2 lg:col-span-3">
          <button class="btn-primary btn-sm" :disabled="saving">{{ saving ? 'Saving…' : 'Save reading' }}</button>
        </div>
      </form>
      <div v-if="lastAlerts.length" class="mt-3 rounded-xl border border-warning-200 bg-warning-50 p-3 text-sm text-warning-800">
        <p class="font-semibold">Alert</p>
        <ul class="list-disc pl-5">
          <li v-for="a in lastAlerts" :key="a">{{ a }}</li>
        </ul>
      </div>
    </SectionCard>

    <div class="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Blood pressure">
        <canvas ref="bpCanvas" class="h-[240px] w-full" />
      </SectionCard>
      <SectionCard title="Heart rate">
        <canvas ref="hrCanvas" class="h-[240px] w-full" />
      </SectionCard>
      <SectionCard title="Glucose" class="lg:col-span-2">
        <canvas ref="gluCanvas" class="h-[240px] w-full" />
      </SectionCard>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import Chart from 'chart.js/auto'
import 'chartjs-adapter-date-fns'

const toast = useToast()
const saving = ref(false)
const lastAlerts = ref([])
const readings = ref([])
let patientId = null

const form = reactive({
  blood_pressure_systolic: null,
  blood_pressure_diastolic: null,
  heart_rate: null,
  glucose_mg_dl: null,
  spo2: null,
  temperature_c: null,
  weight_kg: null,
  notes: '',
})

const bpCanvas = ref(null)
const hrCanvas = ref(null)
const gluCanvas = ref(null)

let bpChart = null
let hrChart = null
let gluChart = null

async function ensurePatientId() {
  if (patientId) return patientId
  const prof = await api.get('/patient/profile')
  patientId = prof.data?.id
  return patientId
}

function toSeries(key) {
  const sorted = [...readings.value].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at))
  return sorted.map(r => ({ x: r.recorded_at, y: r[key] ?? null }))
}

function renderCharts() {
  const common = {
    responsive: true,
    maintainAspectRatio: false,
    parsing: false,
    scales: {
      x: { type: 'time', time: { unit: 'day' } },
      y: { beginAtZero: false },
    },
    plugins: { legend: { display: true } },
  }

  if (bpChart) bpChart.destroy()
  if (hrChart) hrChart.destroy()
  if (gluChart) gluChart.destroy()

  bpChart = new Chart(bpCanvas.value, {
    type: 'line',
    data: {
      datasets: [
        { label: 'Systolic', data: toSeries('blood_pressure_systolic') },
        { label: 'Diastolic', data: toSeries('blood_pressure_diastolic') },
      ],
    },
    options: common,
  })
  hrChart = new Chart(hrCanvas.value, {
    type: 'line',
    data: { datasets: [{ label: 'Heart rate', data: toSeries('heart_rate') }] },
    options: common,
  })
  gluChart = new Chart(gluCanvas.value, {
    type: 'line',
    data: { datasets: [{ label: 'Glucose (mg/dL)', data: toSeries('glucose_mg_dl') }] },
    options: common,
  })
}

async function load() {
  const pid = await ensurePatientId()
  const { data } = await api.get(`/v2/rpm/patients/${pid}/readings`, { params: { limit: 200 } })
  readings.value = data.items || []
  renderCharts()
}

async function submit() {
  saving.value = true
  lastAlerts.value = []
  try {
    const pid = await ensurePatientId()
    const { data } = await api.post(`/v2/rpm/patients/${pid}/readings`, form)
    if (data.alerts?.length) lastAlerts.value = data.alerts
    toast.success('Reading saved')
    await load()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Save failed')
  } finally {
    saving.value = false
  }
}

onMounted(load)
onBeforeUnmount(() => {
  if (bpChart) bpChart.destroy()
  if (hrChart) hrChart.destroy()
  if (gluChart) gluChart.destroy()
})
</script>

