<template>
  <div>
    <PageHeader title="Bills & Payments" subtitle="View your invoices and payment status" />

    <SectionCard title="My Invoices">
      <SkeletonLoader v-if="loading" :rows="5" />
      <DataTable
        v-else
        :columns="columns"
        :data="invoices"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No invoices"
        emptyMessage="Invoices will appear here after completed appointments."
      >
        <template #cell-invoice_number="{ row }">
          <p class="font-medium text-slate-900">{{ row.invoice_number || `#${row.id}` }}</p>
          <p class="text-xs text-slate-500">Appt #{{ row.appointment_id || '—' }}</p>
        </template>
        <template #cell-total="{ row }">
          <span class="font-semibold text-slate-900">₹{{ (row.total ?? 0).toFixed(2) }}</span>
        </template>
        <template #cell-status="{ row }">
          <StatusChip :status="row.status" :label="row.status" />
        </template>
        <template #cell-actions="{ row }">
          <router-link :to="`/patient/invoices/${row.id}/print`" class="btn-ghost btn-sm text-primary-600">
            <Printer class="h-4 w-4" /> Print
          </router-link>
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
import StatusChip from '@/components/StatusChip.vue'
import { Printer } from 'lucide-vue-next'

const loading = ref(true)
const invoices = ref([])
const page = ref(1)

const columns = [
  { key: 'invoice_number', label: 'Invoice' },
  { key: 'total', label: 'Total' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '' },
]

onMounted(async () => {
  const { data } = await api.get('/patient/invoices')
  invoices.value = data || []
  loading.value = false
})
</script>

