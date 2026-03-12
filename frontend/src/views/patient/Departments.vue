<template>
  <div>
    <PageHeader title="Departments" subtitle="Browse hospital departments and find a specialist" />

    <SkeletonLoader v-if="loading" :rows="4" />
    <div v-else class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div
        v-for="d in departments"
        :key="d.id"
        @click="selectDept(d)"
        class="card cursor-pointer p-5 transition hover:border-primary-300 hover:shadow-md"
        :class="selectedDept?.id === d.id ? 'border-primary-400 ring-2 ring-primary-500/20' : ''"
      >
        <div class="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-primary-50">
          <Building2 class="h-5 w-5 text-primary-600" />
        </div>
        <h3 class="font-semibold text-slate-900">{{ d.name }}</h3>
        <p class="mt-1 text-sm text-slate-500 line-clamp-2">{{ d.description || 'Explore doctors in this department' }}</p>
      </div>
    </div>

    <!-- Doctors in selected department -->
    <SectionCard v-if="selectedDept" :title="`Doctors in ${selectedDept.name}`" class="mt-6">
      <DataTable
        :columns="columns"
        :data="doctors"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No doctors available"
        emptyMessage="No doctors are currently listed in this department."
      >
        <template #cell-username="{ row }">
          <span class="font-medium text-slate-900">Dr. {{ row.username }}</span>
        </template>
        <template #cell-actions="{ row }">
          <router-link :to="`/patient/doctors/${row.id}`" class="btn-primary btn-sm">View Profile</router-link>
        </template>
      </DataTable>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { Building2 } from 'lucide-vue-next'

const loading = ref(true)
const departments = ref([])
const selectedDept = ref(null)
const doctors = ref([])
const page = ref(1)

const columns = [
  { key: 'username', label: 'Doctor' },
  { key: 'specialization', label: 'Specialization' },
  { key: 'experience_years', label: 'Experience (yrs)' },
  { key: 'actions', label: '' },
]

async function selectDept(dept) {
  selectedDept.value = dept
  page.value = 1
  const { data } = await api.get('/patient/doctors', { params: { department_id: dept.id } })
  doctors.value = data
}

onMounted(async () => {
  const { data } = await api.get('/patient/departments')
  departments.value = data
  loading.value = false
})
</script>
