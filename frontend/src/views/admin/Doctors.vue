<template>
  <div>
    <PageHeader title="Manage Doctors" subtitle="Add, edit, and manage hospital doctors">
      <template #actions>
        <button @click="toggleForm" class="btn-primary btn-sm">
          <component :is="showForm ? X : Plus" class="h-4 w-4" />
          {{ showForm ? 'Cancel' : 'Add Doctor' }}
        </button>
      </template>
    </PageHeader>

    <!-- Add/Edit Form -->
    <Transition name="fade">
      <SectionCard v-if="showForm" :title="editId ? 'Edit Doctor' : 'Add New Doctor'" class="mb-6">
        <form @submit.prevent="saveDoctor" class="space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <template v-if="!editId">
              <div>
                <label class="label-text">Username</label>
                <input v-model="form.username" class="input-field" placeholder="johndoe" required />
              </div>
              <div>
                <label class="label-text">Email</label>
                <input v-model="form.email" type="email" class="input-field" placeholder="doctor@example.com" required />
              </div>
              <div>
                <label class="label-text">Password</label>
                <input v-model="form.password" type="password" class="input-field" placeholder="Min. 6 characters" required />
              </div>
            </template>
            <div>
              <label class="label-text">Department</label>
              <select v-model="form.department_id" class="select-field">
                <option value="">Select department</option>
                <option v-for="d in departments" :key="d.id" :value="d.id">{{ d.name }}</option>
              </select>
            </div>
            <div>
              <label class="label-text">Specialization</label>
              <input v-model="form.specialization" class="input-field" placeholder="e.g. Cardiology" />
            </div>
            <div>
              <label class="label-text">Phone</label>
              <input v-model="form.phone" class="input-field" placeholder="+91 98765 43210" />
            </div>
            <div>
              <label class="label-text">Qualification</label>
              <input v-model="form.qualification" class="input-field" placeholder="e.g. MBBS, MD" />
            </div>
            <div>
              <label class="label-text">Experience (years)</label>
              <input v-model.number="form.experience_years" type="number" class="input-field" min="0" />
            </div>
          </div>
          <button type="submit" class="btn-primary">{{ editId ? 'Update Doctor' : 'Add Doctor' }}</button>
        </form>
      </SectionCard>
    </Transition>

    <!-- Doctors Table -->
    <DataTable
      :columns="columns"
      :data="filteredDoctors"
      :page="page"
      @update:page="page = $event"
      searchable
      :searchQuery="search"
      @update:searchQuery="onSearch"
      searchPlaceholder="Search doctors by name or specialization..."
      emptyTitle="No doctors found"
    >
      <template #cell-username="{ row }">
        <div class="flex items-center gap-3">
          <div class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-accent-50 text-xs font-bold text-accent-600">
            {{ row.username.charAt(0).toUpperCase() }}
          </div>
          <div>
            <p class="font-medium text-slate-900">Dr. {{ row.username }}</p>
            <p class="text-xs text-slate-500">{{ row.email }}</p>
          </div>
        </div>
      </template>
      <template #cell-department="{ row }">
        {{ row.department || '--' }}
      </template>
      <template #cell-experience_years="{ row }">
        {{ row.experience_years }}y
      </template>
      <template #cell-status="{ row }">
        <button @click="toggleUser(row)" class="cursor-pointer">
          <StatusChip :status="row.is_active ? 'active' : 'blocked'" :label="row.is_active ? 'Active' : 'Blocked'" />
        </button>
      </template>
      <template #cell-actions="{ row }">
        <div class="flex gap-1">
          <button @click="editDoctor(row)" class="btn-ghost btn-sm text-primary-600">Edit</button>
          <button @click="confirmDelete(row.id)" class="btn-ghost btn-sm text-danger-600">Delete</button>
        </div>
      </template>
    </DataTable>

    <ConfirmDialog
      v-model="showDeleteDialog"
      title="Delete Doctor"
      message="Are you sure? This action cannot be undone. Doctors with existing appointments cannot be deleted."
      confirmText="Delete"
      variant="danger"
      @confirm="deleteDoctor"
    />
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import StatusChip from '@/components/StatusChip.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import { Plus, X } from 'lucide-vue-next'

const toast = useToast()
const doctors = ref([])
const departments = ref([])
const search = ref('')
const page = ref(1)
const showForm = ref(false)
const editId = ref(null)
const showDeleteDialog = ref(false)
const deleteTargetId = ref(null)

const form = reactive({
  username: '', email: '', password: '',
  department_id: '', specialization: '', phone: '',
  qualification: '', experience_years: 0,
})

const columns = [
  { key: 'username', label: 'Doctor' },
  { key: 'department', label: 'Department' },
  { key: 'specialization', label: 'Specialization' },
  { key: 'phone', label: 'Phone' },
  { key: 'experience_years', label: 'Exp' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

const filteredDoctors = computed(() => {
  if (!search.value.trim()) return doctors.value
  const q = search.value.toLowerCase()
  return doctors.value.filter(d =>
    d.username.toLowerCase().includes(q) ||
    (d.specialization || '').toLowerCase().includes(q) ||
    (d.department || '').toLowerCase().includes(q)
  )
})

function onSearch(val) {
  search.value = val
  page.value = 1
}

function toggleForm() {
  showForm.value = !showForm.value
  if (!showForm.value) resetForm()
}

function resetForm() {
  Object.assign(form, { username: '', email: '', password: '', department_id: '', specialization: '', phone: '', qualification: '', experience_years: 0 })
  editId.value = null
}

function editDoctor(d) {
  editId.value = d.id
  Object.assign(form, { department_id: d.department_id || '', specialization: d.specialization, phone: d.phone, qualification: d.qualification, experience_years: d.experience_years })
  showForm.value = true
}

async function saveDoctor() {
  try {
    if (editId.value) {
      await api.put(`/admin/doctors/${editId.value}`, form)
      toast.success('Doctor updated')
    } else {
      await api.post('/admin/doctors', form)
      toast.success('Doctor added')
    }
    resetForm()
    showForm.value = false
    fetchDoctors()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Error')
  }
}

function confirmDelete(id) {
  deleteTargetId.value = id
  showDeleteDialog.value = true
}

async function deleteDoctor() {
  try {
    await api.delete(`/admin/doctors/${deleteTargetId.value}`)
    toast.success('Doctor deleted')
    fetchDoctors()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Delete failed')
  }
}

async function toggleUser(d) {
  await api.put(`/admin/users/${d.user_id}/toggle`)
  toast.info(`User ${d.is_active ? 'blocked' : 'activated'}`)
  fetchDoctors()
}

async function fetchDoctors() {
  const { data } = await api.get('/admin/doctors')
  doctors.value = data
}

onMounted(async () => {
  fetchDoctors()
  const { data } = await api.get('/admin/departments')
  departments.value = data
})
</script>
