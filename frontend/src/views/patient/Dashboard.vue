<template>
  <div>
    <PageHeader title="Patient Dashboard" subtitle="Manage your appointments and find doctors" />

    <!-- Appointments Section -->
    <SectionCard title="My Appointments" class="mb-6">
      <template #header>
        <router-link to="/patient/departments" class="btn-primary btn-sm">
          <Plus class="h-4 w-4" /> Book Appointment
        </router-link>
      </template>
      <SkeletonLoader v-if="loading" :rows="3" />
      <DataTable
        v-else
        :columns="aptColumns"
        :data="appointments"
        :page="aptPage"
        @update:page="aptPage = $event"
        emptyTitle="No appointments yet"
        emptyMessage="Book your first appointment by finding a doctor below."
      >
        <template #cell-doctor_name="{ row }">
          <span class="font-medium text-slate-900">Dr. {{ row.doctor_name }}</span>
          <span class="block text-xs text-slate-400">{{ row.specialization }}</span>
        </template>
        <template #cell-date="{ row }">
          <span>{{ formatDate(row.date) }}</span>
          <span class="block text-xs text-slate-400">{{ row.time_slot }}</span>
        </template>
        <template #cell-status="{ row }">
          <StatusChip :status="row.status" :label="row.status" />
        </template>
        <template #cell-actions="{ row }">
          <div class="flex gap-1">
            <template v-if="row.status === 'pending' || row.status === 'confirmed'">
              <button @click="openReschedule(row)" class="btn-ghost btn-sm text-primary-600">Reschedule</button>
              <button @click="confirmCancel(row.id)" class="btn-ghost btn-sm text-danger-600">Cancel</button>
            </template>
            <router-link v-if="row.status === 'completed'" :to="`/patient/appointments/${row.id}/summary`" class="btn-ghost btn-sm text-primary-600">
              <FileText class="h-3.5 w-3.5" /> Summary
            </router-link>
            <span v-if="row.status !== 'pending' && row.status !== 'confirmed' && row.status !== 'completed'" class="text-xs text-slate-400">--</span>
          </div>
        </template>
      </DataTable>
    </SectionCard>

    <!-- Reschedule Card -->
    <SectionCard v-if="rescheduling" title="Reschedule Appointment" class="mb-6">
      <div class="flex flex-col gap-3 sm:flex-row sm:items-end">
        <div>
          <label class="label-text">New Date</label>
          <input v-model="rescheduleForm.date" type="date" class="input-field" :min="today" :max="maxDate" />
        </div>
        <div>
          <label class="label-text">New Time</label>
          <input v-model="rescheduleForm.time_slot" type="time" class="input-field" />
        </div>
        <div class="flex gap-2">
          <button @click="submitReschedule" class="btn-warning btn-sm">Reschedule</button>
          <button @click="rescheduling = null" class="btn-secondary btn-sm">Cancel</button>
        </div>
      </div>
    </SectionCard>

    <!-- Export -->
    <div class="mb-6">
      <button @click="exportHistory" :disabled="exportStatus === 'pending'" class="btn-secondary btn-sm">
        <Download class="h-4 w-4" />
        {{ exportStatus === 'pending' ? 'Exporting...' : 'Export Treatment History' }}
      </button>
    </div>

    <!-- Find a Doctor -->
    <SectionCard title="Find a Doctor" class="mb-6">
      <div class="relative mb-4 max-w-md">
        <Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input v-model="doctorSearch" class="input-field pl-9" placeholder="Search by name or specialization..." @input="searchDoctors" />
      </div>
      <div v-if="searchResults.length" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <router-link
          v-for="d in searchResults"
          :key="d.id"
          :to="`/patient/doctors/${d.id}`"
          class="card flex items-center gap-4 p-4 transition hover:border-primary-300 hover:shadow-md"
        >
          <div class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-accent-50 text-sm font-bold text-accent-600">
            {{ d.username.charAt(0).toUpperCase() }}
          </div>
          <div class="min-w-0">
            <p class="truncate font-medium text-slate-900">Dr. {{ d.username }}</p>
            <p class="truncate text-xs text-slate-500">{{ d.specialization }} &middot; {{ d.department }}</p>
            <p class="text-xs text-slate-400">{{ d.experience_years }} yrs exp</p>
          </div>
        </router-link>
      </div>
    </SectionCard>

    <!-- Departments -->
    <SectionCard title="Departments">
      <div class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        <div
          v-for="dept in departments"
          :key="dept.id"
          @click="toggleDept(dept.id)"
          class="card cursor-pointer p-4 transition hover:border-primary-300 hover:shadow-md"
          :class="expandedDept === dept.id ? 'border-primary-300 ring-1 ring-primary-500/20' : ''"
        >
          <div class="flex items-center gap-3">
            <Building2 class="h-5 w-5 text-primary-500" />
            <h4 class="font-semibold text-slate-900">{{ dept.name }}</h4>
          </div>
          <p class="mt-1 text-xs text-slate-500 line-clamp-2">{{ dept.description }}</p>
          <div v-if="expandedDept === dept.id" class="mt-3 space-y-2 border-t border-slate-100 pt-3">
            <div v-if="deptDoctors[dept.id]?.length">
              <router-link
                v-for="d in deptDoctors[dept.id]"
                :key="d.id"
                :to="`/patient/doctors/${d.id}`"
                class="flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition hover:bg-slate-50"
              >
                <Stethoscope class="h-4 w-4 text-slate-400" />
                <span class="text-slate-700">Dr. {{ d.username }}</span>
                <span class="text-xs text-slate-400">&middot; {{ d.specialization }}</span>
              </router-link>
            </div>
            <p v-else class="text-xs text-slate-400">No doctors in this department yet.</p>
          </div>
        </div>
      </div>
    </SectionCard>

    <ConfirmDialog
      v-model="showCancelDialog"
      title="Cancel Appointment"
      message="Are you sure you want to cancel this appointment? This action cannot be undone."
      confirmText="Cancel Appointment"
      variant="danger"
      @confirm="cancelApt"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import StatusChip from '@/components/StatusChip.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, Search, Download, Building2, Stethoscope, FileText } from 'lucide-vue-next'

const toast = useToast()
const today = new Date().toISOString().slice(0, 10)
const _max = new Date(); _max.setDate(_max.getDate() + 30)
const maxDate = _max.toISOString().slice(0, 10)

const loading = ref(true)
const appointments = ref([])
const aptPage = ref(1)
const rescheduling = ref(null)
const rescheduleForm = reactive({ date: '', time_slot: '' })
const departments = ref([])
const expandedDept = ref(null)
const deptDoctors = ref({})
const doctorSearch = ref('')
const searchResults = ref([])
const exportStatus = ref('')
const showCancelDialog = ref(false)
const cancelTargetId = ref(null)

const aptColumns = [
  { key: 'doctor_name', label: 'Doctor' },
  { key: 'date', label: 'Schedule' },
  { key: 'reason', label: 'Reason' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function openReschedule(a) {
  rescheduling.value = a
  rescheduleForm.date = a.date
  rescheduleForm.time_slot = a.time_slot
}

async function submitReschedule() {
  try {
    await api.put(`/patient/appointments/${rescheduling.value.id}/reschedule`, rescheduleForm)
    toast.success('Appointment rescheduled')
    rescheduling.value = null
    fetchAppointments()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Reschedule failed')
  }
}

function confirmCancel(id) {
  cancelTargetId.value = id
  showCancelDialog.value = true
}

async function cancelApt() {
  await api.put(`/patient/appointments/${cancelTargetId.value}/cancel`)
  toast.success('Appointment cancelled')
  fetchAppointments()
}

async function fetchAppointments() {
  const { data } = await api.get('/patient/appointments')
  appointments.value = data
}

async function exportHistory() {
  exportStatus.value = 'pending'
  try {
    const { data } = await api.post('/patient/export')
    const taskId = data.task_id
    const poll = setInterval(async () => {
      try {
        const res = await api.get(`/patient/export/status/${taskId}`)
        if (res.data.status === 'done') {
          clearInterval(poll)
          exportStatus.value = 'done'
          toast.success('Export complete!')
          setTimeout(() => { exportStatus.value = '' }, 3000)
        }
      } catch { clearInterval(poll); exportStatus.value = 'error'; toast.error('Export failed') }
    }, 2000)
  } catch { exportStatus.value = 'error'; toast.error('Export failed (Redis/Celery may not be running)') }
}

async function searchDoctors() {
  if (!doctorSearch.value.trim()) { searchResults.value = []; return }
  const { data } = await api.get('/patient/doctors', { params: { q: doctorSearch.value } })
  searchResults.value = data
}

async function toggleDept(deptId) {
  if (expandedDept.value === deptId) { expandedDept.value = null; return }
  expandedDept.value = deptId
  if (!deptDoctors.value[deptId]) {
    const { data } = await api.get('/patient/doctors', { params: { department_id: deptId } })
    deptDoctors.value[deptId] = data
  }
}

onMounted(async () => {
  const [_, depts] = await Promise.all([fetchAppointments(), api.get('/patient/departments')])
  departments.value = depts.data
  loading.value = false
})
</script>
