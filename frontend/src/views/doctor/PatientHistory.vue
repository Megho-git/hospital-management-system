<template>
  <div>
    <PageHeader title="Patient Treatment History" subtitle="Review and manage patient records">
      <template #actions>
        <router-link to="/doctor" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back
        </router-link>
      </template>
    </PageHeader>

    <SkeletonLoader v-if="loading" :rows="4" />
    <DataTable
      v-else
      :columns="columns"
      :data="treatments"
      :page="page"
      @update:page="page = $event"
      emptyTitle="No treatment history"
      emptyMessage="No treatment records found for this patient."
    >
      <template #cell-visit_date="{ row }">
        <span class="font-medium text-slate-900">{{ formatDate(row.visit_date) }}</span>
      </template>
      <template #cell-diagnosis="{ row }">
        <span class="line-clamp-2 max-w-xs">{{ row.diagnosis || '--' }}</span>
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
      <template #cell-actions="{ row }">
        <button @click="openEdit(row)" class="btn-ghost btn-sm text-primary-600">Edit</button>
      </template>
    </DataTable>

    <!-- Edit Treatment -->
    <SectionCard v-if="editing" title="Edit Treatment" class="mt-6">
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
          <div>
            <label class="label-text">Medicines</label>
            <input v-model="editForm.medicines" class="input-field" />
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
          <button type="button" @click="editing = null" class="btn-secondary">Cancel</button>
        </div>
      </form>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { ArrowLeft } from 'lucide-vue-next'

const route = useRoute()
const toast = useToast()
const loading = ref(true)
const treatments = ref([])
const page = ref(1)
const editing = ref(null)
const editForm = reactive({ diagnosis: '', prescription: '', medicines: '', visit_type: '', notes: '' })

const columns = [
  { key: 'visit_date', label: 'Date' },
  { key: 'diagnosis', label: 'Diagnosis' },
  { key: 'prescription', label: 'Prescription' },
  { key: 'medicines', label: 'Medicines' },
  { key: 'visit_type', label: 'Type' },
  { key: 'actions', label: '' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function openEdit(t) {
  editing.value = t
  Object.assign(editForm, {
    diagnosis: t.diagnosis || '',
    prescription: t.prescription || '',
    medicines: t.medicines || '',
    visit_type: t.visit_type || '',
    notes: t.notes || '',
  })
}

async function submitEdit() {
  try {
    await api.put(`/doctor/treatments/${editing.value.id}`, editForm)
    toast.success('Treatment updated')
    editing.value = null
    const { data } = await api.get(`/doctor/patients/${route.params.id}/history`)
    treatments.value = data
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Update failed')
  }
}

onMounted(async () => {
  const { data } = await api.get(`/doctor/patients/${route.params.id}/history`)
  treatments.value = data
  loading.value = false
})
</script>
