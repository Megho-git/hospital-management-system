<template>
  <div class="space-y-6">
    <h1 class="text-2xl font-bold text-slate-900">My Prescriptions</h1>
    <p class="text-sm text-slate-500">Track your prescriptions from pending to dispensed.</p>

    <div v-if="!prescriptions.length" class="card text-center py-12 text-slate-400">
      No prescriptions found.
    </div>

    <div v-for="rx in prescriptions" :key="rx.id" class="card">
      <div class="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p class="text-sm font-semibold text-slate-800">Prescription #{{ rx.id }}</p>
          <p class="text-xs text-slate-500">{{ formatDate(rx.created_at) }}</p>
        </div>
        <span
          class="badge"
          :class="{
            'badge-info': rx.status === 'sent' || rx.status === 'pending',
            'badge-success': rx.status === 'fulfilled',
            'badge-warning': rx.status === 'partial',
            'badge-danger': rx.status === 'cancelled',
          }"
        >
          {{ rx.status }}
        </span>
      </div>
      <table class="mt-3 w-full text-sm">
        <thead class="text-xs uppercase text-slate-500">
          <tr><th class="px-2 py-1 text-left">Medication</th><th class="px-2 py-1">Dose</th><th class="px-2 py-1">Frequency</th><th class="px-2 py-1">Duration</th><th class="px-2 py-1">Qty</th></tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr v-for="it in rx.items" :key="it.id">
            <td class="px-2 py-1 font-medium">{{ it.medication_name }}</td>
            <td class="px-2 py-1 text-center">{{ it.dose || '—' }}</td>
            <td class="px-2 py-1 text-center">{{ it.frequency || '—' }}</td>
            <td class="px-2 py-1 text-center">{{ it.duration || '—' }}</td>
            <td class="px-2 py-1 text-center">{{ it.quantity }}</td>
          </tr>
        </tbody>
      </table>
      <div v-if="rx.items.some(i => i.instructions)" class="mt-2 space-y-1">
        <p v-for="ins in rx.items.filter(i => i.instructions)" :key="'ins-' + ins.id" class="text-xs text-slate-500">
          <strong>{{ ins.medication_name }}:</strong> {{ ins.instructions }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'

const prescriptions = ref([])

async function fetchRx() {
  const { data } = await api.get('/v2/pharmacy/prescriptions')
  prescriptions.value = data
}

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(fetchRx)
</script>
