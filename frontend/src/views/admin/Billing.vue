<template>
  <div>
    <PageHeader title="Billing" subtitle="Manage invoices and payments" />

    <SectionCard title="Invoices" class="mb-6">
      <div class="mb-3 flex flex-col gap-3 sm:flex-row sm:items-end">
        <div class="flex-1">
          <label class="label-text">Search</label>
          <input v-model="q" class="input-field" placeholder="Search by invoice # or patient name..." />
        </div>
        <div class="w-full sm:w-48">
          <label class="label-text">Status</label>
          <select v-model="status" class="select-field">
            <option value="">All</option>
            <option value="draft">Draft</option>
            <option value="issued">Issued</option>
            <option value="paid">Paid</option>
            <option value="cancelled">Cancelled</option>
          </select>
        </div>
        <button class="btn-secondary" @click="fetchInvoices">Refresh</button>
      </div>

      <SkeletonLoader v-if="loading" :rows="5" />
      <DataTable
        v-else
        :columns="columns"
        :data="filtered"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No invoices"
        emptyMessage="Invoices will appear when appointments are completed or manually generated."
      >
        <template #cell-invoice_number="{ row }">
          <p class="font-medium text-slate-900">{{ row.invoice_number || '—' }}</p>
          <p class="text-xs text-slate-500">Appt #{{ row.appointment_id || '—' }}</p>
        </template>
        <template #cell-patient_name="{ row }">
          <span class="text-slate-800">{{ row.patient_name || '--' }}</span>
        </template>
        <template #cell-total="{ row }">
          <span class="font-semibold text-slate-900">₹{{ (row.total ?? 0).toFixed(2) }}</span>
        </template>
        <template #cell-status="{ row }">
          <StatusChip :status="row.status" :label="row.status" />
        </template>
        <template #cell-actions="{ row }">
          <div class="flex flex-wrap gap-1 justify-end">
            <router-link :to="`/admin/invoices/${row.id}/print`" class="btn-ghost btn-sm text-primary-600">
              <Printer class="h-4 w-4" /> Print
            </router-link>
            <button v-if="row.status !== 'paid'" class="btn-success btn-sm" @click="markPaid(row)">
              Mark paid
            </button>
          </div>
        </template>
      </DataTable>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import StatusChip from '@/components/StatusChip.vue'
import { Printer } from 'lucide-vue-next'

const toast = useToast()
const loading = ref(true)
const invoices = ref([])
const page = ref(1)
const q = ref('')
const status = ref('')

const columns = [
  { key: 'invoice_number', label: 'Invoice' },
  { key: 'patient_name', label: 'Patient' },
  { key: 'total', label: 'Total', align: 'right' },
  { key: 'status', label: 'Status' },
  { key: 'actions', label: '', align: 'right' },
]

const filtered = computed(() => {
  let list = invoices.value
  if (status.value) list = list.filter(i => i.status === status.value)
  if (q.value.trim()) {
    const s = q.value.toLowerCase()
    list = list.filter(i =>
      (i.invoice_number || '').toLowerCase().includes(s) ||
      (i.patient_name || '').toLowerCase().includes(s)
    )
  }
  return list
})

async function fetchInvoices() {
  loading.value = true
  try {
    const { data } = await api.get('/admin/invoices')
    invoices.value = data || []
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Failed to load invoices')
  } finally {
    loading.value = false
  }
}

async function markPaid(inv) {
  try {
    await api.put(`/admin/invoices/${inv.id}/pay`)
    toast.success('Marked as paid')
    fetchInvoices()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Payment update failed')
  }
}

onMounted(fetchInvoices)
</script>

