<template>
  <div>
    <PageHeader title="Doctor Dashboard" subtitle="Manage your appointments and patients">
      <template #actions>
        <router-link to="/doctor/availability" class="btn-primary btn-sm">
          <Clock class="h-4 w-4" /> Set Availability
        </router-link>
      </template>
    </PageHeader>

    <SkeletonLoader v-if="loading" :rows="5" />
    <template v-else>
      <!-- Upcoming Appointments -->
      <SectionCard title="Upcoming Appointments" class="mb-6">
        <DataTable
          :columns="upcomingCols"
          :data="appointments"
          :page="upPage"
          @update:page="upPage = $event"
          emptyTitle="No upcoming appointments"
          emptyMessage="You have no scheduled appointments at this time."
        >
          <template #cell-patient_name="{ row }">
            <span class="font-medium text-slate-900">{{ row.patient_name }}</span>
          </template>
          <template #cell-date="{ row }">
            <span>{{ formatDate(row.date) }}</span>
            <span class="block text-xs text-slate-400">{{ row.time_slot }}</span>
          </template>
          <template #cell-status="{ row }">
            <StatusChip :status="row.status" :label="row.status" />
          </template>
          <template #cell-actions="{ row }">
            <div class="flex flex-wrap gap-1">
              <button v-if="row.status === 'pending'" @click="confirmApt(row.id)" class="btn-primary btn-sm">Confirm</button>
              <button @click="openLabs(row)" class="btn-secondary btn-sm">Labs</button>
              <button @click="openComplete(row)" class="btn-success btn-sm">Complete</button>
              <button @click="markNoShow(row.id)" class="btn-ghost btn-sm text-slate-500">No-show</button>
              <button @click="confirmCancel(row.id)" class="btn-ghost btn-sm text-danger-600">Cancel</button>
            </div>
          </template>
        </DataTable>
      </SectionCard>

      <!-- Lab Orders -->
      <SectionCard v-if="labsApt" title="Lab Orders" class="mb-6">
        <div class="mb-3 flex items-center justify-between">
          <p class="text-sm text-slate-500">
            Appointment #{{ labsApt.id }} &middot; {{ labsApt.patient_name }} &middot; {{ formatDate(labsApt.date) }} {{ labsApt.time_slot }}
          </p>
          <button class="btn-secondary btn-sm" @click="labsApt = null">Close</button>
        </div>

        <div class="grid gap-4 lg:grid-cols-2">
          <div class="rounded-xl border border-slate-200 p-4">
            <h4 class="mb-2 text-sm font-semibold text-slate-900">Order new tests</h4>
            <div class="relative">
              <input v-model="labSearch" class="input-field" placeholder="Search lab tests..." @input="searchLabTests" />
              <div v-if="labSearch.trim() && labTestResults.length" class="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg">
                <button
                  v-for="t in labTestResults"
                  :key="t.id"
                  type="button"
                  class="flex w-full items-start justify-between gap-3 px-3 py-2 text-left hover:bg-slate-50"
                  @click="addLabTest(t)"
                >
                  <div class="min-w-0">
                    <p class="truncate text-sm font-medium text-slate-900">{{ t.name }}</p>
                    <p class="truncate text-xs text-slate-500">{{ t.category || '' }}</p>
                  </div>
                  <span class="text-xs text-primary-600">Add</span>
                </button>
              </div>
            </div>

            <div v-if="selectedLabTests.length" class="mt-3 space-y-2">
              <div v-for="t in selectedLabTests" :key="t.id" class="flex items-center justify-between rounded-lg border border-slate-200 p-2">
                <div class="min-w-0">
                  <p class="truncate text-sm font-medium text-slate-900">{{ t.name }}</p>
                  <p class="text-xs text-slate-500">{{ t.category || '' }}</p>
                </div>
                <button class="btn-ghost btn-sm text-slate-500" @click="removeLabTest(t.id)" type="button">
                  <X class="h-4 w-4" />
                </button>
              </div>
              <button class="btn-primary btn-sm" type="button" @click="submitLabOrders" :disabled="orderingLabs">
                <Loader2 v-if="orderingLabs" class="h-4 w-4 animate-spin" />
                {{ orderingLabs ? 'Ordering...' : 'Order Selected Tests' }}
              </button>
            </div>
            <p v-else class="mt-3 text-xs text-slate-500">Search and add tests to order them for this appointment.</p>
          </div>

          <div class="rounded-xl border border-slate-200 p-4">
            <h4 class="mb-2 text-sm font-semibold text-slate-900">Existing orders</h4>
            <SkeletonLoader v-if="loadingLabOrders" :rows="3" />
            <div v-else-if="labOrders.length" class="space-y-3">
              <div v-for="o in labOrders" :key="o.id" class="rounded-xl border border-slate-200 p-3">
                <div class="flex items-start justify-between gap-3">
                  <div class="min-w-0">
                    <p class="truncate font-semibold text-slate-900">{{ o.lab_test?.name || 'Lab Test' }}</p>
                    <p class="text-xs text-slate-500">{{ o.lab_test?.category || '' }}</p>
                  </div>
                  <select v-model="o.status" class="select-field !py-1 !text-sm" @change="updateLabOrder(o)">
                    <option value="ordered">ordered</option>
                    <option value="collected">collected</option>
                    <option value="resulted">resulted</option>
                    <option value="cancelled">cancelled</option>
                  </select>
                </div>
                <div class="mt-2 grid grid-cols-1 gap-2 sm:grid-cols-2">
                  <div>
                    <label class="label-text">Result value</label>
                    <input v-model="o.result_value" class="input-field" placeholder="e.g. 96" @blur="updateLabOrder(o)" />
                    <p v-if="o.lab_test?.normal_range" class="mt-1 text-xs text-slate-500">Range: {{ o.lab_test.normal_range }} {{ o.lab_test.unit || '' }}</p>
                  </div>
                  <div>
                    <label class="label-text">Result notes</label>
                    <input v-model="o.result_notes" class="input-field" placeholder="optional" @blur="updateLabOrder(o)" />
                  </div>
                </div>
              </div>
            </div>
            <EmptyState v-else title="No lab orders" message="Order investigations to track results and follow-ups." :icon="ClipboardList" />
          </div>
        </div>
      </SectionCard>

      <!-- Complete Appointment Form -->
      <SectionCard v-if="completing" title="Complete Appointment" class="mb-6">
        <p class="mb-3 text-sm text-slate-500">Patient: <strong>{{ completing.patient_name }}</strong> &middot; Appointment #{{ completing.id }}</p>
        <div class="mb-4 rounded-xl border border-slate-200 bg-slate-50/50 p-4">
          <div class="mb-3 flex items-center justify-between">
            <h3 class="text-sm font-semibold text-slate-900">Record Vitals</h3>
            <span v-if="vitalsSaved" class="text-xs font-medium text-success-700">Saved</span>
          </div>
          <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            <div>
              <label class="label-text">Temperature (°C)</label>
              <input v-model.number="vitalsForm.temperature" type="number" step="0.1" class="input-field" placeholder="e.g. 37.0" />
            </div>
            <div>
              <label class="label-text">BP Systolic</label>
              <input v-model.number="vitalsForm.blood_pressure_systolic" type="number" class="input-field" placeholder="e.g. 120" />
            </div>
            <div>
              <label class="label-text">BP Diastolic</label>
              <input v-model.number="vitalsForm.blood_pressure_diastolic" type="number" class="input-field" placeholder="e.g. 80" />
            </div>
            <div>
              <label class="label-text">Pulse</label>
              <input v-model.number="vitalsForm.pulse_rate" type="number" class="input-field" placeholder="e.g. 72" />
            </div>
            <div>
              <label class="label-text">SpO₂ (%)</label>
              <input v-model.number="vitalsForm.spo2" type="number" class="input-field" placeholder="e.g. 98" />
            </div>
            <div>
              <label class="label-text">Respiratory rate</label>
              <input v-model.number="vitalsForm.respiratory_rate" type="number" class="input-field" placeholder="e.g. 16" />
            </div>
            <div class="sm:col-span-2 lg:col-span-3">
              <label class="label-text">Vitals notes</label>
              <textarea v-model="vitalsForm.notes" class="input-field" rows="2" placeholder="Any observations..." />
            </div>
          </div>
          <div class="mt-3 flex gap-2">
            <button type="button" class="btn-secondary btn-sm" @click="saveVitals" :disabled="savingVitals">
              <Loader2 v-if="savingVitals" class="h-4 w-4 animate-spin" />
              {{ savingVitals ? 'Saving...' : 'Save Vitals' }}
            </button>
            <p class="text-xs text-slate-500 self-center">Vitals are optional but recommended before completion.</p>
          </div>
        </div>

        <!-- AI Assist actions (hidden when AI is disabled) -->
        <div v-if="aiEnabled" class="mb-4 flex flex-wrap gap-2 rounded-xl border border-indigo-200 bg-indigo-50/50 p-3">
          <span class="text-xs font-semibold text-indigo-600 self-center">AI Assist:</span>
          <button type="button" class="btn-sm rounded-lg border border-indigo-300 bg-white px-3 text-xs font-medium text-indigo-700 hover:bg-indigo-100" @click="aiSuggestRx" :disabled="aiLoading">
            <Loader2 v-if="aiLoading === 'rx'" class="inline h-3 w-3 animate-spin mr-1" />Suggest Meds
          </button>
          <button type="button" class="btn-sm rounded-lg border border-indigo-300 bg-white px-3 text-xs font-medium text-indigo-700 hover:bg-indigo-100" @click="aiSummarize" :disabled="aiLoading">
            <Loader2 v-if="aiLoading === 'summary'" class="inline h-3 w-3 animate-spin mr-1" />Summarize History
          </button>
          <button type="button" class="btn-sm rounded-lg border border-indigo-300 bg-white px-3 text-xs font-medium text-indigo-700 hover:bg-indigo-100" @click="aiGenerateNote" :disabled="aiLoading">
            <Loader2 v-if="aiLoading === 'note'" class="inline h-3 w-3 animate-spin mr-1" />Generate Note
          </button>
        </div>
        <div v-if="aiResult" class="mb-4 rounded-xl border border-slate-200 bg-slate-50 p-3">
          <div class="mb-1 flex items-center justify-between">
            <span class="text-xs font-semibold text-slate-600">AI Result</span>
            <button type="button" class="text-xs text-slate-400 hover:text-slate-600" @click="aiResult = ''">Dismiss</button>
          </div>
          <pre class="whitespace-pre-wrap text-sm text-slate-700 max-h-60 overflow-y-auto">{{ aiResult }}</pre>
        </div>

        <form @submit.prevent="submitComplete" class="space-y-3">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="label-text">Diagnosis</label>
              <textarea v-model="treatmentForm.diagnosis" class="input-field" rows="2" />
            </div>
            <div>
              <label class="label-text">Prescription</label>
              <textarea v-model="treatmentForm.prescription" class="input-field" rows="2" />
            </div>
            <div class="sm:col-span-2">
              <label class="label-text">Prescribe medicines (catalog)</label>
              <div class="relative">
                <input
                  v-model="medSearch"
                  class="input-field"
                  placeholder="Search medication catalog (name, generic, strength...)"
                  @input="searchMeds"
                />
                <div
                  v-if="medSearch.trim() && medResults.length"
                  class="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
                >
                  <button
                    v-for="m in medResults"
                    :key="m.id"
                    type="button"
                    class="flex w-full items-start justify-between gap-3 px-3 py-2 text-left hover:bg-slate-50"
                    @click="addPrescribed(treatmentForm.prescribed_medicines, m)"
                  >
                    <div class="min-w-0">
                      <p class="truncate text-sm font-medium text-slate-900">{{ m.name }} <span class="text-slate-500">{{ m.strength || '' }}</span></p>
                      <p v-if="m.generic_name" class="truncate text-xs text-slate-500">{{ m.generic_name }}</p>
                    </div>
                    <span class="text-xs text-primary-600">Add</span>
                  </button>
                </div>
              </div>

              <div v-if="treatmentForm.prescribed_medicines.length" class="mt-3 space-y-2">
                <div
                  v-for="(pm, idx) in treatmentForm.prescribed_medicines"
                  :key="pm.medication_id"
                  class="rounded-xl border border-slate-200 p-3"
                >
                  <div class="mb-2 flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-semibold text-slate-900">{{ pm.name }}</p>
                      <p class="text-xs text-slate-500">{{ [pm.form, pm.strength, pm.manufacturer].filter(Boolean).join(' • ') }}</p>
                    </div>
                    <button type="button" class="btn-ghost btn-sm text-slate-500" @click="treatmentForm.prescribed_medicines.splice(idx, 1)">
                      <X class="h-4 w-4" />
                    </button>
                  </div>
                  <div class="grid grid-cols-1 gap-3 sm:grid-cols-4">
                    <div>
                      <label class="label-text">Dose</label>
                      <input v-model="pm.dose" class="input-field" placeholder="e.g. 1 tab" />
                    </div>
                    <div>
                      <label class="label-text">Frequency</label>
                      <input v-model="pm.frequency" class="input-field" placeholder="e.g. BID" />
                    </div>
                    <div>
                      <label class="label-text">Duration</label>
                      <input v-model="pm.duration" class="input-field" placeholder="e.g. 5 days" />
                    </div>
                    <div>
                      <label class="label-text">Instructions</label>
                      <input v-model="pm.instructions" class="input-field" placeholder="after food" />
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-3">
                <label class="label-text">Legacy free-text (optional)</label>
                <input v-model="treatmentForm.medicines" class="input-field" placeholder="e.g. Paracetamol 500mg, Amoxicillin 250mg" />
              </div>
            </div>
            <div>
              <label class="label-text">Visit Type</label>
              <select v-model="treatmentForm.visit_type" class="select-field">
                <option value="">Select type</option>
                <option>Initial Consultation</option>
                <option>Follow-up</option>
                <option>Emergency</option>
                <option>Routine Checkup</option>
              </select>
            </div>
            <div class="sm:col-span-2">
              <label class="label-text">Notes</label>
              <textarea v-model="treatmentForm.notes" class="input-field" rows="2" />
            </div>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-success">Save & Complete</button>
            <button type="button" @click="completing = null" class="btn-secondary">Cancel</button>
          </div>
        </form>
      </SectionCard>

      <!-- Appointment History -->
      <SectionCard title="Appointment History" class="mb-6">
        <DataTable
          :columns="historyCols"
          :data="history"
          :page="histPage"
          @update:page="histPage = $event"
          emptyTitle="No appointment history"
          emptyMessage="Completed appointments will appear here."
        >
          <template #cell-patient_name="{ row }">
            <span class="font-medium text-slate-900">{{ row.patient_name }}</span>
          </template>
          <template #cell-date="{ row }">
            <span>{{ formatDate(row.date) }}</span>
            <span class="block text-xs text-slate-400">{{ row.time_slot }}</span>
          </template>
          <template #cell-status="{ row }">
            <StatusChip :status="row.status" :label="row.status" />
          </template>
          <template #cell-treatment="{ row }">
            <template v-if="treatments[row.id]">
              <p class="max-w-xs truncate text-sm">{{ treatments[row.id].diagnosis || '--' }}</p>
              <div class="mt-1 flex gap-2">
                <button @click="openEdit(row.id, treatments[row.id])" class="text-xs font-medium text-primary-600 hover:text-primary-700">Edit</button>
                <button
                  v-if="treatments[row.id].prescribed_medicines?.length"
                  @click="sendToPharmacy(treatments[row.id].id)"
                  class="inline-flex items-center gap-1 text-xs font-medium text-accent-600 hover:text-accent-700"
                >
                  <Send class="h-3 w-3" /> Pharmacy
                </button>
              </div>
            </template>
            <span v-else class="text-xs text-slate-400">No treatment record</span>
          </template>
        </DataTable>
      </SectionCard>

      <!-- Edit Treatment Form -->
      <SectionCard v-if="editingId" title="Edit Treatment" class="mb-6">
        <form @submit.prevent="submitEdit" class="space-y-3">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="label-text">Diagnosis</label>
              <textarea v-model="editForm.diagnosis" class="input-field" rows="2" />
            </div>
            <div>
              <label class="label-text">Prescription</label>
              <textarea v-model="editForm.prescription" class="input-field" rows="2" />
            </div>
            <div class="sm:col-span-2">
              <label class="label-text">Prescribe medicines (catalog)</label>
              <div class="relative">
                <input
                  v-model="editMedSearch"
                  class="input-field"
                  placeholder="Search medication catalog..."
                  @input="searchMedsEdit"
                />
                <div
                  v-if="editMedSearch.trim() && medResultsEdit.length"
                  class="absolute z-20 mt-1 w-full overflow-hidden rounded-xl border border-slate-200 bg-white shadow-lg"
                >
                  <button
                    v-for="m in medResultsEdit"
                    :key="m.id"
                    type="button"
                    class="flex w-full items-start justify-between gap-3 px-3 py-2 text-left hover:bg-slate-50"
                    @click="addPrescribed(editForm.prescribed_medicines, m)"
                  >
                    <div class="min-w-0">
                      <p class="truncate text-sm font-medium text-slate-900">{{ m.name }} <span class="text-slate-500">{{ m.strength || '' }}</span></p>
                      <p v-if="m.generic_name" class="truncate text-xs text-slate-500">{{ m.generic_name }}</p>
                    </div>
                    <span class="text-xs text-primary-600">Add</span>
                  </button>
                </div>
              </div>

              <div v-if="editForm.prescribed_medicines.length" class="mt-3 space-y-2">
                <div
                  v-for="(pm, idx) in editForm.prescribed_medicines"
                  :key="pm.medication_id"
                  class="rounded-xl border border-slate-200 p-3"
                >
                  <div class="mb-2 flex items-start justify-between gap-3">
                    <div class="min-w-0">
                      <p class="truncate text-sm font-semibold text-slate-900">{{ pm.name }}</p>
                      <p class="text-xs text-slate-500">{{ [pm.form, pm.strength, pm.manufacturer].filter(Boolean).join(' • ') }}</p>
                    </div>
                    <button type="button" class="btn-ghost btn-sm text-slate-500" @click="editForm.prescribed_medicines.splice(idx, 1)">
                      <X class="h-4 w-4" />
                    </button>
                  </div>
                  <div class="grid grid-cols-1 gap-3 sm:grid-cols-4">
                    <div>
                      <label class="label-text">Dose</label>
                      <input v-model="pm.dose" class="input-field" />
                    </div>
                    <div>
                      <label class="label-text">Frequency</label>
                      <input v-model="pm.frequency" class="input-field" />
                    </div>
                    <div>
                      <label class="label-text">Duration</label>
                      <input v-model="pm.duration" class="input-field" />
                    </div>
                    <div>
                      <label class="label-text">Instructions</label>
                      <input v-model="pm.instructions" class="input-field" />
                    </div>
                  </div>
                </div>
              </div>

              <div class="mt-3">
                <label class="label-text">Legacy free-text (optional)</label>
                <input v-model="editForm.medicines" class="input-field" />
              </div>
            </div>
            <div>
              <label class="label-text">Visit Type</label>
              <input v-model="editForm.visit_type" class="input-field" />
            </div>
            <div class="sm:col-span-2">
              <label class="label-text">Notes</label>
              <textarea v-model="editForm.notes" class="input-field" rows="2" />
            </div>
          </div>
          <div class="flex gap-2 pt-2">
            <button type="submit" class="btn-primary">Save Changes</button>
            <button type="button" @click="editingId = null" class="btn-secondary">Cancel</button>
          </div>
        </form>
      </SectionCard>

      <!-- Assigned Patients -->
      <SectionCard title="Assigned Patients">
        <div v-if="patients.length" class="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          <router-link
            v-for="p in patients"
            :key="p.id"
            :to="`/doctor/patients/${p.id}/history`"
            class="card flex items-center gap-3 p-4 transition hover:border-primary-300 hover:shadow-md"
          >
            <div class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-accent-50 text-sm font-bold text-accent-600">
              {{ p.username.charAt(0).toUpperCase() }}
            </div>
            <div class="min-w-0 flex-1">
              <p class="truncate font-medium text-slate-900">{{ p.username }}</p>
              <p class="text-xs text-slate-500">View treatment history</p>
              <div class="mt-1 flex flex-wrap gap-1">
                <span
                  v-if="(p.allergies || '').trim()"
                  class="inline-flex items-center rounded-full bg-warning-50 px-2 py-0.5 text-[11px] font-semibold text-warning-700 ring-1 ring-warning-500/20"
                  title="Allergies"
                >
                  Allergies
                </span>
                <span
                  v-if="(p.chronic_conditions || '').trim()"
                  class="inline-flex items-center rounded-full bg-danger-50 px-2 py-0.5 text-[11px] font-semibold text-danger-700 ring-1 ring-danger-500/20"
                  title="Chronic conditions"
                >
                  Chronic
                </span>
              </div>
            </div>
          </router-link>
        </div>
        <EmptyState v-else title="No patients yet" message="Patients will appear here once they book appointments with you." :icon="Users" />
      </SectionCard>
    </template>

    <ConfirmDialog
      v-model="showCancelDialog"
      title="Cancel Appointment"
      message="Are you sure you want to cancel this appointment?"
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
import EmptyState from '@/components/EmptyState.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Clock, Users, X, Loader2, ClipboardList, Send } from 'lucide-vue-next'

const toast = useToast()
const loading = ref(true)
const appointments = ref([])
const history = ref([])
const treatments = ref({})
const patients = ref([])
const upPage = ref(1)
const histPage = ref(1)

const completing = ref(null)
const treatmentForm = reactive({ diagnosis: '', prescription: '', medicines: '', visit_type: '', notes: '', prescribed_medicines: [] })
const editingId = ref(null)
const editTreatmentId = ref(null)
const editForm = reactive({ diagnosis: '', prescription: '', medicines: '', visit_type: '', notes: '', prescribed_medicines: [] })
const showCancelDialog = ref(false)
const cancelTargetId = ref(null)

const medSearch = ref('')
const medResults = ref([])
const editMedSearch = ref('')
const medResultsEdit = ref([])

const vitalsSaved = ref(false)
const savingVitals = ref(false)
const vitalsForm = reactive({
  temperature: null,
  blood_pressure_systolic: null,
  blood_pressure_diastolic: null,
  pulse_rate: null,
  spo2: null,
  respiratory_rate: null,
  notes: '',
})

const aiEnabled = ref(false)
const aiLoading = ref(false)
const aiResult = ref('')

const labsApt = ref(null)
const labSearch = ref('')
const labTestResults = ref([])
const selectedLabTests = ref([])
const orderingLabs = ref(false)
const labOrders = ref([])
const loadingLabOrders = ref(false)

const upcomingCols = [
  { key: 'patient_name', label: 'Patient' },
  { key: 'date', label: 'Schedule' },
  { key: 'reason', label: 'Reason' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

const historyCols = [
  { key: 'patient_name', label: 'Patient' },
  { key: 'date', label: 'Schedule' },
  { key: 'status', label: 'Status' },
  { key: 'treatment', label: 'Treatment' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

async function confirmApt(id) {
  await api.put(`/doctor/appointments/${id}/confirm`)
  toast.success('Appointment confirmed')
  fetchData()
}

async function markNoShow(id) {
  await api.put(`/doctor/appointments/${id}/no-show`)
  toast.info('Marked as no-show')
  fetchData()
}

function openComplete(apt) {
  completing.value = apt
  Object.assign(treatmentForm, { diagnosis: '', prescription: '', medicines: '', visit_type: '', notes: '', prescribed_medicines: [] })
  medSearch.value = ''
  medResults.value = []
  vitalsSaved.value = false
  Object.assign(vitalsForm, {
    temperature: null,
    blood_pressure_systolic: null,
    blood_pressure_diastolic: null,
    pulse_rate: null,
    spo2: null,
    respiratory_rate: null,
    notes: '',
  })
  loadVitals(apt.id)
}

async function loadVitals(aptId) {
  try {
    const { data } = await api.get(`/doctor/appointments/${aptId}/vitals`)
    if (data) {
      Object.assign(vitalsForm, {
        temperature: data.temperature ?? null,
        blood_pressure_systolic: data.blood_pressure_systolic ?? null,
        blood_pressure_diastolic: data.blood_pressure_diastolic ?? null,
        pulse_rate: data.pulse_rate ?? null,
        spo2: data.spo2 ?? null,
        respiratory_rate: data.respiratory_rate ?? null,
        notes: data.notes || '',
      })
      vitalsSaved.value = true
    }
  } catch {
    // ignore
  }
}

async function saveVitals() {
  if (!completing.value) return
  savingVitals.value = true
  try {
    await api.post(`/doctor/appointments/${completing.value.id}/vitals`, vitalsForm)
    vitalsSaved.value = true
    toast.success('Vitals saved')
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Failed to save vitals')
  } finally {
    savingVitals.value = false
  }
}

async function submitComplete() {
  if (!vitalsSaved.value) {
    await saveVitals()
  }
  const { data } = await api.put(`/doctor/appointments/${completing.value.id}/complete`, treatmentForm)
  toast.success('Appointment completed')
  const treatmentId = data?.treatment?.id
  completing.value = null
  await fetchData()
  if (treatmentId && treatmentForm.prescribed_medicines.length) {
    sendToPharmacy(treatmentId)
  }
}

async function sendToPharmacy(treatmentId) {
  try {
    await api.post('/v2/pharmacy/prescriptions', { treatment_id: treatmentId })
    toast.success('Prescription sent to pharmacy')
  } catch (e) {
    const msg = e.response?.data?.msg || 'Failed to send to pharmacy'
    if (e.response?.status === 409) {
      toast.info('Prescription already sent for this treatment')
    } else {
      toast.error(msg)
    }
  }
}

function openLabs(apt) {
  labsApt.value = apt
  labSearch.value = ''
  labTestResults.value = []
  selectedLabTests.value = []
  fetchLabOrders()
}

let _labTimer = null
async function searchLabTests() {
  clearTimeout(_labTimer)
  _labTimer = setTimeout(async () => {
    const q = labSearch.value.trim()
    if (!q) { labTestResults.value = []; return }
    const { data } = await api.get('/doctor/lab-tests', { params: { q } })
    labTestResults.value = data || []
  }, 200)
}

function addLabTest(t) {
  if (selectedLabTests.value.some(x => x.id === t.id)) return
  selectedLabTests.value.push(t)
  labSearch.value = ''
  labTestResults.value = []
}

function removeLabTest(id) {
  selectedLabTests.value = selectedLabTests.value.filter(x => x.id !== id)
}

async function submitLabOrders() {
  if (!labsApt.value || !selectedLabTests.value.length) return
  orderingLabs.value = true
  try {
    await api.post(`/doctor/appointments/${labsApt.value.id}/lab-orders`, {
      lab_test_ids: selectedLabTests.value.map(x => x.id),
    })
    toast.success('Lab orders created')
    selectedLabTests.value = []
    fetchLabOrders()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Failed to create lab orders')
  } finally {
    orderingLabs.value = false
  }
}

async function fetchLabOrders() {
  if (!labsApt.value) return
  loadingLabOrders.value = true
  try {
    const { data } = await api.get(`/doctor/appointments/${labsApt.value.id}/lab-orders`)
    labOrders.value = data || []
  } finally {
    loadingLabOrders.value = false
  }
}

let _updateOrderTimer = null
async function updateLabOrder(o) {
  clearTimeout(_updateOrderTimer)
  _updateOrderTimer = setTimeout(async () => {
    try {
      await api.put(`/doctor/lab-orders/${o.id}`, {
        status: o.status,
        result_value: o.result_value,
        result_notes: o.result_notes,
      })
      toast.success('Lab order updated')
    } catch (e) {
      toast.error(e.response?.data?.msg || 'Update failed')
    }
  }, 150)
}

function confirmCancel(id) {
  cancelTargetId.value = id
  showCancelDialog.value = true
}

async function cancelApt() {
  await api.put(`/doctor/appointments/${cancelTargetId.value}/cancel`)
  toast.success('Appointment cancelled')
  fetchData()
}

function openEdit(aptId, treatment) {
  editingId.value = aptId
  editTreatmentId.value = treatment.id
  Object.assign(editForm, {
    diagnosis: treatment.diagnosis || '',
    prescription: treatment.prescription || '',
    medicines: treatment.medicines || '',
    visit_type: treatment.visit_type || '',
    notes: treatment.notes || '',
    prescribed_medicines: (treatment.prescribed_medicines || []).map(pm => ({
      medication_id: pm.medication_id,
      name: pm.name,
      generic_name: pm.generic_name,
      form: pm.form,
      strength: pm.strength,
      manufacturer: pm.manufacturer,
      dose: pm.dose || '',
      frequency: pm.frequency || '',
      duration: pm.duration || '',
      instructions: pm.instructions || '',
    })),
  })
  editMedSearch.value = ''
  medResultsEdit.value = []
}

async function submitEdit() {
  try {
    await api.put(`/doctor/treatments/${editTreatmentId.value}`, editForm)
    toast.success('Treatment updated')
    editingId.value = null
    fetchData()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Update failed')
  }
}

let _medSearchTimer = null
async function searchMeds() {
  clearTimeout(_medSearchTimer)
  _medSearchTimer = setTimeout(async () => {
    const q = medSearch.value.trim()
    if (!q) { medResults.value = []; return }
    const { data } = await api.get('/doctor/medications', { params: { q } })
    medResults.value = data
  }, 200)
}

let _medSearchTimerEdit = null
async function searchMedsEdit() {
  clearTimeout(_medSearchTimerEdit)
  _medSearchTimerEdit = setTimeout(async () => {
    const q = editMedSearch.value.trim()
    if (!q) { medResultsEdit.value = []; return }
    const { data } = await api.get('/doctor/medications', { params: { q } })
    medResultsEdit.value = data
  }, 200)
}

function addPrescribed(targetList, med) {
  if (targetList.some(x => x.medication_id === med.id)) return
  targetList.push({
    medication_id: med.id,
    name: med.name,
    generic_name: med.generic_name,
    form: med.form,
    strength: med.strength,
    manufacturer: med.manufacturer,
    dose: '',
    frequency: '',
    duration: '',
    instructions: '',
  })
  medSearch.value = ''
  editMedSearch.value = ''
  medResults.value = []
  medResultsEdit.value = []
}

async function aiSuggestRx() {
  if (!completing.value) return
  aiLoading.value = 'rx'
  try {
    const { data } = await api.post('/v2/ai/suggest-prescription', {
      patient_id: completing.value.patient_id,
      diagnosis: treatmentForm.diagnosis,
    })
    if (Array.isArray(data.suggestions)) {
      aiResult.value = JSON.stringify(data.suggestions, null, 2)
      for (const s of data.suggestions) {
        if (s.medication_id && !treatmentForm.prescribed_medicines.some(p => p.medication_id === s.medication_id)) {
          treatmentForm.prescribed_medicines.push({
            medication_id: s.medication_id,
            name: s.name || `Med #${s.medication_id}`,
            dose: s.dose || '',
            frequency: s.frequency || '',
            duration: s.duration || '',
            instructions: s.reason || '',
          })
        }
      }
    } else {
      aiResult.value = typeof data.suggestions === 'string' ? data.suggestions : JSON.stringify(data.suggestions)
    }
  } catch (e) {
    toast.error(e.response?.data?.msg || 'AI suggestion failed')
  } finally {
    aiLoading.value = false
  }
}

async function aiSummarize() {
  if (!completing.value) return
  aiLoading.value = 'summary'
  try {
    const { data } = await api.post('/v2/ai/summarize-history', { patient_id: completing.value.patient_id })
    aiResult.value = data.summary
  } catch (e) {
    toast.error(e.response?.data?.msg || 'AI summary failed')
  } finally {
    aiLoading.value = false
  }
}

async function aiGenerateNote() {
  if (!completing.value) return
  aiLoading.value = 'note'
  try {
    const { data } = await api.post('/v2/ai/generate-note', {
      patient_id: completing.value.patient_id,
      diagnosis: treatmentForm.diagnosis,
      prescription: treatmentForm.prescription,
      visit_type: treatmentForm.visit_type,
      notes_draft: treatmentForm.notes,
    })
    aiResult.value = data.note
    if (!treatmentForm.notes && data.note) {
      treatmentForm.notes = data.note
    }
  } catch (e) {
    toast.error(e.response?.data?.msg || 'AI note generation failed')
  } finally {
    aiLoading.value = false
  }
}

async function checkAiStatus() {
  try {
    const { data } = await api.get('/v2/ai/status')
    aiEnabled.value = data.enabled === true
  } catch {
    aiEnabled.value = false
  }
}

async function fetchData() {
  const { data } = await api.get('/doctor/dashboard')
  appointments.value = data.appointments
  history.value = data.history || []
  treatments.value = data.treatments || {}
  patients.value = data.patients
}

onMounted(async () => {
  await fetchData()
  loading.value = false
  checkAiStatus()
})
</script>
