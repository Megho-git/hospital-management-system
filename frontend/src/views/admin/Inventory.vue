<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">Pharmacy Inventory</h1>

    <!-- Alert cards -->
    <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div class="card border-l-4 border-amber-500">
        <p class="text-xs font-semibold uppercase text-amber-600">Low Stock Items</p>
        <p class="mt-1 text-2xl font-bold text-amber-700">{{ lowStockItems.length }}</p>
        <ul v-if="lowStockItems.length" class="mt-2 max-h-28 space-y-1 overflow-y-auto text-xs text-slate-600">
          <li v-for="a in lowStockItems" :key="a.id">{{ a.medication_name }} — {{ a.total_on_hand }} left</li>
        </ul>
      </div>
      <div class="card border-l-4 border-red-500">
        <p class="text-xs font-semibold uppercase text-red-600">Expiring Soon / Expired</p>
        <p class="mt-1 text-2xl font-bold text-red-700">{{ expiryAlerts.length }}</p>
        <ul v-if="expiryAlerts.length" class="mt-2 max-h-28 space-y-1 overflow-y-auto text-xs text-slate-600">
          <li v-for="a in expiryAlerts" :key="a.id">
            {{ a.drug_item?.medication_name }} — batch {{ a.batch_number }}
            <span :class="a.alert === 'expired' ? 'text-red-600 font-bold' : 'text-amber-600'">
              ({{ a.alert === 'expired' ? 'EXPIRED' : 'expires ' + a.expiry_date }})
            </span>
          </li>
        </ul>
      </div>
      <div class="card border-l-4 border-blue-500">
        <p class="text-xs font-semibold uppercase text-blue-600">Pending Prescriptions</p>
        <p class="mt-1 text-2xl font-bold text-blue-700">{{ pendingRx.length }}</p>
      </div>
    </div>

    <!-- Drug inventory table -->
    <div class="card">
      <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 class="text-lg font-semibold text-slate-800">Drug Items</h2>
        <div class="flex gap-2">
          <input v-model="search" placeholder="Search drugs…" class="input w-48" @input="fetchDrugs" />
          <button class="btn btn-primary" @click="showAdd = true">+ Add Drug</button>
        </div>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th class="px-3 py-2 text-left">Name</th><th class="px-3 py-2 text-left">Form</th><th class="px-3 py-2">SKU</th><th class="px-3 py-2">On-Hand</th><th class="px-3 py-2">Reorder</th><th class="px-3 py-2">Actions</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="d in drugs" :key="d.id" class="hover:bg-slate-50">
              <td class="px-3 py-2 font-medium">{{ d.medication_name }} <span class="text-xs text-slate-400">{{ d.strength }}</span></td>
              <td class="px-3 py-2">{{ d.form || '—' }}</td>
              <td class="px-3 py-2 text-center font-mono text-xs">{{ d.sku }}</td>
              <td class="px-3 py-2 text-center" :class="d.total_on_hand <= d.reorder_level ? 'text-red-600 font-bold' : ''">{{ d.total_on_hand }}</td>
              <td class="px-3 py-2 text-center">{{ d.reorder_level }}</td>
              <td class="px-3 py-2 text-center space-x-1">
                <button class="btn-ghost btn-sm" @click="openLots(d)">Lots</button>
                <button class="btn-ghost btn-sm" @click="openReceive(d)">Receive</button>
              </td>
            </tr>
            <tr v-if="!drugs.length"><td colspan="6" class="py-6 text-center text-slate-400">No drug items yet.</td></tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Pending prescriptions -->
    <div class="card" v-if="pendingRx.length">
      <h2 class="mb-4 text-lg font-semibold text-slate-800">Pending Prescriptions</h2>
      <div class="overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th class="px-3 py-2 text-left">Rx #</th><th class="px-3 py-2 text-left">Patient</th><th class="px-3 py-2 text-left">Doctor</th><th class="px-3 py-2 text-left">Medications</th><th class="px-3 py-2">Status</th><th class="px-3 py-2">Actions</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="rx in pendingRx" :key="rx.id" class="hover:bg-slate-50">
              <td class="px-3 py-2 font-mono text-xs">#{{ rx.id }}</td>
              <td class="px-3 py-2">Patient #{{ rx.patient_id }}</td>
              <td class="px-3 py-2">Doctor #{{ rx.doctor_id }}</td>
              <td class="px-3 py-2">
                <span v-for="(it, idx) in rx.items" :key="it.id">{{ it.medication_name }} x{{ it.quantity }}<span v-if="idx < rx.items.length - 1">, </span></span>
              </td>
              <td class="px-3 py-2 text-center"><span class="badge badge-info">{{ rx.status }}</span></td>
              <td class="px-3 py-2 text-center">
                <button class="btn btn-primary btn-sm" @click="dispense(rx)" :disabled="dispensing">Dispense</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add drug modal -->
    <div v-if="showAdd" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="showAdd = false">
      <div class="card w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">Add Drug Item</h3>
        <label class="label">Medication</label>
        <select v-model="addForm.medication_id" class="input mb-3">
          <option value="">Select…</option>
          <option v-for="m in allMeds" :key="m.id" :value="m.id">{{ m.name }} {{ m.strength || '' }} ({{ m.form || '—' }})</option>
        </select>
        <label class="label">SKU</label>
        <input v-model="addForm.sku" class="input mb-3" />
        <label class="label">Reorder Level</label>
        <input v-model.number="addForm.reorder_level" type="number" class="input mb-4" />
        <div class="flex justify-end gap-2">
          <button class="btn" @click="showAdd = false">Cancel</button>
          <button class="btn btn-primary" @click="addDrug" :disabled="!addForm.medication_id">Save</button>
        </div>
      </div>
    </div>

    <!-- Lots modal -->
    <div v-if="lotsModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="lotsModal = null">
      <div class="card w-full max-w-lg max-h-[80vh] overflow-y-auto">
        <h3 class="text-lg font-semibold mb-4">Stock Lots — {{ lotsModal.medication_name }}</h3>
        <table class="w-full text-sm mb-4">
          <thead class="bg-slate-50 text-xs uppercase text-slate-500">
            <tr><th class="px-2 py-1">Batch</th><th class="px-2 py-1">Expiry</th><th class="px-2 py-1">Qty</th><th class="px-2 py-1">Cost</th></tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="l in lots" :key="l.id">
              <td class="px-2 py-1 font-mono text-xs">{{ l.batch_number || '—' }}</td>
              <td class="px-2 py-1" :class="isExpired(l.expiry_date) ? 'text-red-600 font-bold' : ''">{{ l.expiry_date || '—' }}</td>
              <td class="px-2 py-1 text-center">{{ l.quantity_on_hand }}</td>
              <td class="px-2 py-1 text-center">{{ l.unit_cost?.toFixed(2) }}</td>
            </tr>
            <tr v-if="!lots.length"><td colspan="4" class="py-4 text-center text-slate-400">No lots.</td></tr>
          </tbody>
        </table>
        <button class="btn" @click="lotsModal = null">Close</button>
      </div>
    </div>

    <!-- Receive lot modal -->
    <div v-if="receiveModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/40" @click.self="receiveModal = null">
      <div class="card w-full max-w-md">
        <h3 class="text-lg font-semibold mb-4">Receive Stock — {{ receiveModal.medication_name }}</h3>
        <label class="label">Batch Number</label>
        <input v-model="rcvForm.batch_number" class="input mb-3" />
        <label class="label">Expiry Date</label>
        <input v-model="rcvForm.expiry_date" type="date" class="input mb-3" />
        <label class="label">Quantity</label>
        <input v-model.number="rcvForm.quantity" type="number" class="input mb-3" />
        <label class="label">Unit Cost</label>
        <input v-model.number="rcvForm.unit_cost" type="number" step="0.01" class="input mb-4" />
        <div class="flex justify-end gap-2">
          <button class="btn" @click="receiveModal = null">Cancel</button>
          <button class="btn btn-primary" @click="receiveLot" :disabled="!rcvForm.quantity">Receive</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const drugs = ref([])
const search = ref('')
const lowStockItems = ref([])
const expiryAlerts = ref([])
const pendingRx = ref([])
const allMeds = ref([])
const dispensing = ref(false)

const showAdd = ref(false)
const addForm = ref({ medication_id: '', sku: '', reorder_level: 10 })

const lotsModal = ref(null)
const lots = ref([])

const receiveModal = ref(null)
const rcvForm = ref({ batch_number: '', expiry_date: '', quantity: 0, unit_cost: 0 })

async function fetchDrugs() {
  const { data } = await api.get('/v2/pharmacy/drugs', { params: { q: search.value } })
  drugs.value = data
}

async function fetchAlerts() {
  const [ls, ex] = await Promise.all([
    api.get('/v2/pharmacy/alerts/low-stock'),
    api.get('/v2/pharmacy/alerts/expiry'),
  ])
  lowStockItems.value = ls.data
  expiryAlerts.value = ex.data
}

async function fetchPendingRx() {
  const { data } = await api.get('/v2/pharmacy/prescriptions', { params: { status: 'sent' } })
  pendingRx.value = data
}

async function fetchMeds() {
  try {
    const { data } = await api.get('/admin/medications')
    allMeds.value = data
  } catch { /* may not exist yet */ }
}

async function addDrug() {
  await api.post('/v2/pharmacy/drugs', addForm.value)
  showAdd.value = false
  addForm.value = { medication_id: '', sku: '', reorder_level: 10 }
  fetchDrugs()
  fetchAlerts()
}

async function openLots(drug) {
  lotsModal.value = drug
  const { data } = await api.get(`/v2/pharmacy/drugs/${drug.id}/lots`)
  lots.value = data
}

function openReceive(drug) {
  receiveModal.value = drug
  rcvForm.value = { batch_number: '', expiry_date: '', quantity: 0, unit_cost: 0 }
}

async function receiveLot() {
  await api.post(`/v2/pharmacy/drugs/${receiveModal.value.id}/lots`, rcvForm.value)
  receiveModal.value = null
  fetchDrugs()
  fetchAlerts()
}

async function dispense(rx) {
  dispensing.value = true
  try {
    await api.post(`/v2/pharmacy/prescriptions/${rx.id}/dispense`)
    fetchPendingRx()
    fetchDrugs()
    fetchAlerts()
  } finally {
    dispensing.value = false
  }
}

function isExpired(d) {
  if (!d) return false
  return new Date(d) < new Date()
}

onMounted(() => {
  fetchDrugs()
  fetchAlerts()
  fetchPendingRx()
  fetchMeds()
})
</script>
