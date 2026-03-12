<template>
  <div>
    <PageHeader title="Audit Log" subtitle="Trace critical actions for compliance and accountability" />

    <SectionCard title="Filters" class="mb-6">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div>
          <label class="label-text">Action contains</label>
          <input v-model="filters.action" class="input-field" placeholder="e.g. invoice, appointment" />
        </div>
        <div>
          <label class="label-text">Resource type</label>
          <input v-model="filters.resource_type" class="input-field" placeholder="e.g. invoice" />
        </div>
        <div>
          <label class="label-text">User ID</label>
          <input v-model.number="filters.user_id" type="number" class="input-field" placeholder="optional" />
        </div>
        <div class="flex items-end gap-2">
          <button class="btn-primary" @click="fetchLog">Apply</button>
          <button class="btn-secondary" @click="reset">Reset</button>
        </div>
      </div>
    </SectionCard>

    <SectionCard title="Entries">
      <SkeletonLoader v-if="loading" :rows="6" />
      <DataTable
        v-else
        :columns="columns"
        :data="items"
        :page="page"
        @update:page="page = $event; fetchLog()"
        emptyTitle="No audit entries"
        emptyMessage="Actions will appear here as users operate the system."
      >
        <template #cell-created_at="{ row }">
          <span class="text-sm text-slate-800">{{ formatDateTime(row.created_at) }}</span>
        </template>
        <template #cell-user="{ row }">
          <span class="text-sm text-slate-800">{{ row.username || '—' }}</span>
          <span class="block text-xs text-slate-400">ID: {{ row.user_id || '—' }}</span>
        </template>
        <template #cell-action="{ row }">
          <p class="font-medium text-slate-900">{{ row.action }}</p>
          <p class="text-xs text-slate-500">{{ row.ip_address || '' }}</p>
        </template>
        <template #cell-resource="{ row }">
          <span class="text-sm text-slate-800">{{ row.resource_type || '—' }} #{{ row.resource_id || '—' }}</span>
        </template>
        <template #cell-details="{ row }">
          <p class="line-clamp-2 max-w-md text-xs text-slate-600">{{ row.details || '—' }}</p>
        </template>
      </DataTable>

      <div class="mt-3 flex items-center justify-between text-xs text-slate-500">
        <span>Total: {{ total }}</span>
        <div class="flex gap-2">
          <button class="btn-secondary btn-sm" :disabled="page <= 1" @click="page--; fetchLog()">Prev</button>
          <button class="btn-secondary btn-sm" :disabled="page * perPage >= total" @click="page++; fetchLog()">Next</button>
        </div>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const loading = ref(true)
const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 25

const filters = reactive({ action: '', resource_type: '', user_id: null })

const columns = [
  { key: 'created_at', label: 'Time' },
  { key: 'user', label: 'User' },
  { key: 'action', label: 'Action' },
  { key: 'resource', label: 'Resource' },
  { key: 'details', label: 'Details' },
]

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function fetchLog() {
  loading.value = true
  const params = { page: page.value, per_page: perPage }
  if (filters.action) params.action = filters.action
  if (filters.resource_type) params.resource_type = filters.resource_type
  if (filters.user_id) params.user_id = filters.user_id
  const { data } = await api.get('/admin/audit-log', { params })
  items.value = data.items || []
  total.value = data.total || 0
  loading.value = false
}

function reset() {
  filters.action = ''
  filters.resource_type = ''
  filters.user_id = null
  page.value = 1
  fetchLog()
}

onMounted(fetchLog)
</script>

