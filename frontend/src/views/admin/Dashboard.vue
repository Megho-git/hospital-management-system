<template>
  <div>
    <PageHeader title="Admin Dashboard" subtitle="Hospital overview and quick actions" />

    <SkeletonLoader v-if="loading" :rows="5" />
    <template v-else>
      <!-- Stats Grid -->
      <div class="mb-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
        <StatCard label="Doctors" :value="stats.doctors || 0" :icon="Stethoscope" iconBg="bg-accent-50" iconColor="text-accent-600" />
        <StatCard label="Patients" :value="stats.patients || 0" :icon="Users" iconBg="bg-success-50" iconColor="text-success-600" />
        <StatCard label="Appointments" :value="stats.appointments || 0" :icon="CalendarDays" iconBg="bg-primary-50" iconColor="text-primary-600" />
        <StatCard label="Departments" :value="stats.departments || 0" :icon="Building2" iconBg="bg-warning-50" iconColor="text-warning-600" />
        <StatCard label="Medications" :value="stats.medications || 0" :icon="Pill" iconBg="bg-primary-50" iconColor="text-primary-700" />
        <StatCard label="Completion rate" :value="`${stats.appointment_completion_rate || 0}%`" :icon="ClipboardList" iconBg="bg-slate-100" iconColor="text-slate-700" />
        <StatCard label="Revenue (MTD)" :value="`₹${(stats.revenue_mtd ?? revenueMtd).toFixed(0)}`" :icon="Receipt" iconBg="bg-success-50" iconColor="text-success-700" />
      </div>

      <!-- Recent Doctors & Patients -->
      <div class="mb-6 grid gap-6 lg:grid-cols-2">
        <SectionCard title="Recent Doctors">
          <div class="space-y-3">
            <div v-for="d in doctors.slice(0, 5)" :key="d.id" class="flex items-center justify-between rounded-lg bg-slate-50/50 px-3 py-2">
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-accent-50 text-xs font-bold text-accent-600">
                  {{ d.username.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-900">Dr. {{ d.username }}</p>
                  <p class="text-xs text-slate-500">{{ d.specialization || 'No specialization' }}</p>
                </div>
              </div>
              <StatusChip :status="d.is_active ? 'active' : 'blocked'" :label="d.is_active ? 'Active' : 'Blocked'" />
            </div>
            <EmptyState v-if="!doctors.length" title="No doctors" message="Add your first doctor to get started." :icon="Stethoscope" />
          </div>
        </SectionCard>

        <SectionCard title="Recent Patients">
          <div class="space-y-3">
            <div v-for="p in patients.slice(0, 5)" :key="p.id" class="flex items-center justify-between rounded-lg bg-slate-50/50 px-3 py-2">
              <div class="flex items-center gap-3">
                <div class="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-success-50 text-xs font-bold text-success-600">
                  {{ p.username.charAt(0).toUpperCase() }}
                </div>
                <div>
                  <p class="text-sm font-medium text-slate-900">{{ p.username }}</p>
                  <p class="text-xs text-slate-500">{{ p.email }}</p>
                </div>
              </div>
              <StatusChip :status="p.is_active ? 'active' : 'blocked'" :label="p.is_active ? 'Active' : 'Blocked'" />
            </div>
            <EmptyState v-if="!patients.length" title="No patients" message="Patients will appear when they register." :icon="Users" />
          </div>
        </SectionCard>
      </div>

      <!-- Upcoming Appointments -->
      <SectionCard title="Upcoming Appointments" class="mb-6">
        <DataTable
          :columns="aptColumns"
          :data="appointments.slice(0, 10)"
          emptyTitle="No appointments"
          emptyMessage="No appointments have been booked yet."
        >
          <template #cell-patient_name="{ row }">
            <span class="font-medium text-slate-900">{{ row.patient_name }}</span>
          </template>
          <template #cell-doctor_name="{ row }">
            <span>Dr. {{ row.doctor_name }}</span>
          </template>
          <template #cell-date="{ row }">
            <span>{{ formatDate(row.date) }}</span>
            <span class="block text-xs text-slate-400">{{ row.time_slot }}</span>
          </template>
          <template #cell-status="{ row }">
            <StatusChip :status="row.status" :label="row.status" />
          </template>
        </DataTable>
      </SectionCard>

      <!-- Recent Activity -->
      <SectionCard title="Recent Activity" class="mb-6">
        <div v-if="stats.recent_activity?.length" class="space-y-2">
          <div
            v-for="a in stats.recent_activity.slice(0, 10)"
            :key="a.id"
            class="flex items-start justify-between gap-3 rounded-xl border border-slate-200 bg-white p-3"
          >
            <div class="min-w-0">
              <p class="truncate text-sm font-semibold text-slate-900">{{ a.action }}</p>
              <p class="text-xs text-slate-500">
                {{ a.username || 'Unknown' }} &middot; {{ a.resource_type || '—' }} #{{ a.resource_id || '—' }}
              </p>
              <p v-if="a.details" class="mt-1 line-clamp-2 text-xs text-slate-600">{{ a.details }}</p>
            </div>
            <span class="shrink-0 text-xs text-slate-400">{{ formatDateTime(a.created_at) }}</span>
          </div>
        </div>
        <p v-else class="text-sm text-slate-500">No recent activity yet.</p>
      </SectionCard>

      <!-- Export Section -->
      <SectionCard title="Data Export">
        <div class="flex flex-wrap gap-3">
          <button @click="triggerExport('appointments')" class="btn-secondary btn-sm">
            <Download class="h-4 w-4" /> Export Appointments
          </button>
          <button @click="triggerExport('doctors')" class="btn-secondary btn-sm">
            <Download class="h-4 w-4" /> Export Doctors
          </button>
          <button @click="triggerExport('patients')" class="btn-secondary btn-sm">
            <Download class="h-4 w-4" /> Export Patients
          </button>
        </div>
        <p v-if="exportMsg" class="mt-2 text-xs text-slate-500">{{ exportMsg }}</p>
      </SectionCard>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import StatCard from '@/components/StatCard.vue'
import DataTable from '@/components/DataTable.vue'
import StatusChip from '@/components/StatusChip.vue'
import EmptyState from '@/components/EmptyState.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { Stethoscope, Users, CalendarDays, Building2, Download, Receipt, Pill, ClipboardList } from 'lucide-vue-next'

const toast = useToast()
const loading = ref(true)
const stats = ref({})
const doctors = ref([])
const patients = ref([])
const appointments = ref([])
const exportMsg = ref('')
const revenueMtd = ref(0)

const aptColumns = [
  { key: 'patient_name', label: 'Patient' },
  { key: 'doctor_name', label: 'Doctor' },
  { key: 'date', label: 'Schedule' },
  { key: 'status', label: 'Status' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function triggerExport(type) {
  exportMsg.value = 'Starting export...'
  try {
    await api.post(`/admin/export/${type}`)
    exportMsg.value = 'Export started. Check instance/exports/ folder.'
    toast.success(`${type} export started`)
  } catch {
    exportMsg.value = ''
    toast.error('Export failed (Redis/Celery may not be running)')
  }
}

onMounted(async () => {
  const [s, d, p, a] = await Promise.all([
    api.get('/admin/stats'),
    api.get('/admin/doctors'),
    api.get('/admin/patients'),
    api.get('/admin/appointments'),
  ])
  stats.value = s.data
  doctors.value = d.data
  patients.value = p.data
  appointments.value = a.data
  try {
    const res = await api.get('/admin/invoices')
    const now = new Date()
    const start = new Date(now.getFullYear(), now.getMonth(), 1)
    revenueMtd.value = (res.data || [])
      .filter(inv => inv.status === 'paid' && inv.paid_at && new Date(inv.paid_at) >= start)
      .reduce((sum, inv) => sum + (Number(inv.total) || 0), 0)
  } catch { revenueMtd.value = 0 }
  loading.value = false
})
</script>
