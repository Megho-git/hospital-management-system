<template>
  <div>
    <!-- Screen header (hidden when printing) -->
    <div class="mb-6 flex items-center justify-between print:hidden">
      <PageHeader title="Appointment Summary" subtitle="Print or save this document for your records" />
      <div class="flex gap-2">
        <button @click="printPage" class="btn-primary btn-sm">
          <Printer class="h-4 w-4" /> Print
        </button>
        <router-link :to="`/telemedicine/appointments/${route.params.id}`" class="btn-secondary btn-sm">
          <Video class="h-4 w-4" /> Telemedicine
        </router-link>
        <router-link to="/patient" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back
        </router-link>
      </div>
    </div>

    <SkeletonLoader v-if="loading" :rows="6" />

    <div v-else-if="data" class="mx-auto max-w-2xl">
      <!-- Printable document -->
      <div class="card p-8 print:border-0 print:shadow-none">
        <!-- Header -->
        <div class="mb-6 flex items-start justify-between border-b border-slate-200 pb-6">
          <div>
            <h1 class="text-xl font-bold text-primary-700">MedFlow HMS</h1>
            <p class="text-sm text-slate-500">Hospital Management System</p>
          </div>
          <div class="text-right">
            <p class="text-xs text-slate-400">Appointment #{{ data.id }}</p>
            <StatusChip :status="data.status" :label="data.status" />
          </div>
        </div>

        <!-- Appointment Info -->
        <div class="mb-6 grid grid-cols-2 gap-4">
          <div>
            <p class="text-xs font-semibold uppercase text-slate-400">Date</p>
            <p class="text-sm font-medium text-slate-900">{{ formatDate(data.date) }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase text-slate-400">Time</p>
            <p class="text-sm font-medium text-slate-900">{{ data.time_slot }}</p>
          </div>
          <div>
            <p class="text-xs font-semibold uppercase text-slate-400">Reason</p>
            <p class="text-sm text-slate-700">{{ data.reason || 'N/A' }}</p>
          </div>
        </div>

        <!-- Doctor & Patient -->
        <div class="mb-6 grid grid-cols-2 gap-6">
          <div class="rounded-lg bg-slate-50 p-4">
            <h3 class="mb-2 text-xs font-bold uppercase text-slate-400">Doctor</h3>
            <p class="font-semibold text-slate-900">Dr. {{ data.doctor_name }}</p>
            <p class="text-sm text-slate-600">{{ data.doctor_department || '' }}</p>
            <p class="text-sm text-slate-500">{{ data.doctor_qualification || '' }}</p>
            <p class="text-sm text-slate-500">{{ data.doctor_phone || '' }}</p>
          </div>
          <div class="rounded-lg bg-slate-50 p-4">
            <h3 class="mb-2 text-xs font-bold uppercase text-slate-400">Patient</h3>
            <p class="font-semibold text-slate-900">{{ data.patient_name }}</p>
            <p class="text-sm text-slate-500">{{ data.patient_email }}</p>
            <p class="text-sm text-slate-500">{{ data.patient_phone || '' }}</p>
            <p v-if="data.patient_blood_group" class="text-sm text-slate-500">Blood: {{ data.patient_blood_group }}</p>
            <p v-if="data.patient_allergies" class="mt-2 text-sm text-warning-700">
              <span class="font-semibold">Allergies:</span> {{ data.patient_allergies }}
            </p>
            <p v-if="data.patient_chronic_conditions" class="mt-1 text-sm text-danger-700">
              <span class="font-semibold">Chronic:</span> {{ data.patient_chronic_conditions }}
            </p>
          </div>
        </div>

        <!-- Treatment Record -->
        <div v-if="data.treatment" class="rounded-lg border border-slate-200 p-4">
          <h3 class="mb-3 text-sm font-bold uppercase text-slate-600">Treatment Record</h3>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <p class="text-xs font-semibold text-slate-400">Diagnosis</p>
              <p class="text-sm text-slate-800">{{ data.treatment.diagnosis || 'N/A' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400">Visit Type</p>
              <p class="text-sm text-slate-800">{{ data.treatment.visit_type || 'N/A' }}</p>
            </div>
            <div class="sm:col-span-2">
              <p class="text-xs font-semibold text-slate-400">Prescription</p>
              <p class="text-sm text-slate-800">{{ data.treatment.prescription || 'N/A' }}</p>
            </div>
            <div class="sm:col-span-2">
              <p class="text-xs font-semibold text-slate-400">Medicines</p>
              <div v-if="data.treatment.prescribed_medicines?.length" class="mt-1 space-y-1">
                <div v-for="pm in data.treatment.prescribed_medicines" :key="pm.id || pm.medication_id" class="text-sm text-slate-800">
                  <span class="font-medium">{{ pm.name }}</span>
                  <span class="text-slate-500"> {{ pm.strength || '' }}</span>
                  <span class="text-slate-600"> — {{ [pm.dose, pm.frequency, pm.duration].filter(Boolean).join(' • ') }}</span>
                  <span v-if="pm.instructions" class="block text-xs text-slate-500">{{ pm.instructions }}</span>
                </div>
              </div>
              <div v-else-if="data.treatment.medicines" class="flex flex-wrap gap-1 mt-1">
                <span
                  v-for="med in data.treatment.medicines.split(',')"
                  :key="med"
                  class="rounded-full bg-primary-50 px-2 py-0.5 text-xs font-medium text-primary-700 print:bg-transparent print:border print:border-slate-300"
                >{{ med.trim() }}</span>
              </div>
              <p v-else class="text-sm text-slate-500">N/A</p>
            </div>
            <div class="sm:col-span-2">
              <p class="text-xs font-semibold text-slate-400">Notes</p>
              <p class="text-sm text-slate-800">{{ data.treatment.notes || 'N/A' }}</p>
            </div>
          </div>
        </div>
        <div v-else class="rounded-lg border border-dashed border-slate-300 p-4 text-center">
          <p class="text-sm text-slate-500">No treatment record yet. This will be updated after your visit.</p>
        </div>

        <!-- Vitals -->
        <div class="mt-6 rounded-lg border border-slate-200 p-4">
          <h3 class="mb-3 text-sm font-bold uppercase text-slate-600">Vitals</h3>
          <div v-if="data.vitals" class="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p class="text-xs font-semibold text-slate-400">Temperature</p>
              <p class="text-slate-800">{{ data.vitals.temperature != null ? `${data.vitals.temperature}°C` : '—' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400">Blood Pressure</p>
              <p class="text-slate-800">
                <span v-if="data.vitals.blood_pressure_systolic && data.vitals.blood_pressure_diastolic">
                  {{ data.vitals.blood_pressure_systolic }}/{{ data.vitals.blood_pressure_diastolic }}
                </span>
                <span v-else>—</span>
              </p>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400">Pulse</p>
              <p class="text-slate-800">{{ data.vitals.pulse_rate != null ? data.vitals.pulse_rate : '—' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400">SpO₂</p>
              <p class="text-slate-800">{{ data.vitals.spo2 != null ? `${data.vitals.spo2}%` : '—' }}</p>
            </div>
            <div>
              <p class="text-xs font-semibold text-slate-400">Respiratory rate</p>
              <p class="text-slate-800">{{ data.vitals.respiratory_rate != null ? data.vitals.respiratory_rate : '—' }}</p>
            </div>
            <div v-if="data.vitals.notes" class="col-span-2">
              <p class="text-xs font-semibold text-slate-400">Notes</p>
              <p class="text-slate-800">{{ data.vitals.notes }}</p>
            </div>
          </div>
          <p v-else class="text-sm text-slate-500">No vitals recorded for this appointment.</p>
        </div>

        <!-- Lab Orders -->
        <div class="mt-6 rounded-lg border border-slate-200 p-4">
          <h3 class="mb-3 text-sm font-bold uppercase text-slate-600">Lab Orders</h3>
          <div v-if="data.lab_orders?.length" class="space-y-3">
            <div v-for="o in data.lab_orders" :key="o.id" class="rounded-xl border border-slate-200 p-3">
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate font-semibold text-slate-900">{{ o.lab_test?.name || 'Lab Test' }}</p>
                  <p class="text-xs text-slate-500">{{ o.lab_test?.category || '' }}</p>
                </div>
                <StatusChip :status="o.status" :label="o.status" />
              </div>
              <div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2 text-sm">
                <div>
                  <p class="text-xs font-semibold text-slate-400">Result</p>
                  <p class="text-slate-800">
                    {{ o.result_value || '—' }}
                    <span v-if="o.lab_test?.unit" class="text-slate-500">{{ o.lab_test.unit }}</span>
                  </p>
                  <p v-if="o.lab_test?.normal_range" class="text-xs text-slate-500">Range: {{ o.lab_test.normal_range }}</p>
                </div>
                <div v-if="o.result_notes">
                  <p class="text-xs font-semibold text-slate-400">Notes</p>
                  <p class="text-slate-800">{{ o.result_notes }}</p>
                </div>
              </div>
            </div>
          </div>
          <p v-else class="text-sm text-slate-500">No lab orders for this appointment.</p>
        </div>

        <!-- Footer -->
        <div class="mt-8 border-t border-slate-200 pt-4 text-center">
          <p class="text-xs text-slate-400">
            Generated on {{ new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' }) }}
            &middot; MedFlow Hospital Management System
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import StatusChip from '@/components/StatusChip.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { ArrowLeft, Printer, Video } from 'lucide-vue-next'

const route = useRoute()
const loading = ref(true)
const data = ref(null)

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' })
}

function printPage() {
  window.print()
}

onMounted(async () => {
  try {
    const res = await api.get(`/patient/appointments/${route.params.id}/summary`)
    data.value = res.data
  } catch {
    data.value = null
  } finally {
    loading.value = false
  }
})
</script>
