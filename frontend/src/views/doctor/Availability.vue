<template>
  <div>
    <PageHeader title="Set Availability" subtitle="Configure your available time slots for the next 30 days">
      <template #actions>
        <router-link to="/doctor" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back
        </router-link>
      </template>
    </PageHeader>

    <!-- Compact weekly pattern editor -->
    <SectionCard title="Weekly Schedule" class="mb-6">
      <p class="mb-3 text-sm text-slate-500">
        Define your recurring weekly pattern. We'll automatically generate slots for the next 30 days from this template.
      </p>
      <div class="space-y-2">
        <div
          v-for="(day, idx) in days"
          :key="idx"
          class="flex items-start gap-3 rounded-lg border border-slate-100 bg-slate-50/60 px-3 py-2"
        >
          <div class="mt-1 min-w-[80px] text-xs font-semibold uppercase tracking-wide text-slate-500">
            {{ day.label }}
          </div>
          <div class="flex-1 space-y-1.5">
            <div
              v-for="(slot, si) in day.slots"
              :key="si"
              class="flex flex-wrap items-center gap-1.5"
            >
              <input v-model="slot.start" type="time" class="input-field w-[110px]" />
              <span class="text-slate-400">–</span>
              <input v-model="slot.end" type="time" class="input-field w-[110px]" />
              <button
                @click="day.slots.splice(si, 1)"
                class="btn-icon text-danger-500 hover:text-danger-600"
                title="Remove interval"
              >
                <X class="h-3 w-3" />
              </button>
            </div>
            <button
              @click="day.slots.push({ start: '09:00', end: '17:00' })"
              class="btn-ghost btn-xs text-primary-600"
              type="button"
            >
              <Plus class="h-3 w-3" /> Add interval
            </button>
          </div>
        </div>
      </div>
      <div class="mt-4 flex flex-wrap items-center justify-between gap-3">
        <p class="text-xs text-slate-500">
          Saving will overwrite availability for the next 30 days using this weekly pattern.
        </p>
        <button @click="save" class="btn-primary">
          <Save class="h-4 w-4" /> Save Availability
        </button>
      </div>
    </SectionCard>

    <!-- Current availability -->
    <SectionCard title="Current Availability">
      <DataTable
        :columns="columns"
        :data="current"
        :page="page"
        @update:page="page = $event"
        emptyTitle="No availability set"
        emptyMessage="Add time slots above and save to set your availability."
      >
        <template #cell-date="{ row }">
          <span class="font-medium text-slate-900">{{ formatDate(row.date) }}</span>
        </template>
      </DataTable>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import DataTable from '@/components/DataTable.vue'
import { ArrowLeft, Plus, X, Save } from 'lucide-vue-next'

const toast = useToast()
const days = ref([])
const current = ref([])
const page = ref(1)

const columns = [
  { key: 'date', label: 'Date' },
  { key: 'start_time', label: 'Start' },
  { key: 'end_time', label: 'End' },
]

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

function initDays() {
  // Weekly template starting Monday → Sunday
  const weekdayMeta = [
    { weekday: 1, label: 'Mon' },
    { weekday: 2, label: 'Tue' },
    { weekday: 3, label: 'Wed' },
    { weekday: 4, label: 'Thu' },
    { weekday: 5, label: 'Fri' },
    { weekday: 6, label: 'Sat' },
    { weekday: 0, label: 'Sun' },
  ]
  return weekdayMeta.map(d => ({
    weekday: d.weekday,
    label: d.label,
    slots: [],
  }))
}

async function save() {
  const slots = []
  const today = new Date()

  // Expand weekly pattern into concrete dates for the next 30 days
  for (let i = 0; i < 30; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() + i)
    const weekday = d.getDay()
    const tpl = days.value.find(day => day.weekday === weekday)
    if (!tpl || !tpl.slots.length) continue

    const iso = d.toISOString().slice(0, 10)
    for (const s of tpl.slots) {
      if (s.start && s.end) {
        slots.push({ date: iso, start_time: s.start, end_time: s.end })
      }
    }
  }
  await api.post('/doctor/availability', { slots })
  toast.success('Availability saved!')
  fetchCurrent()
}

async function fetchCurrent() {
  const { data } = await api.get('/doctor/availability')
  current.value = data
}

onMounted(() => {
  days.value = initDays()
  fetchCurrent()
})
</script>
