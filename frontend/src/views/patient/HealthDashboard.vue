<template>
  <div>
    <PageHeader title="Health Dashboard" subtitle="Your unified health timeline, labs, and vitals" />

    <div class="grid gap-4 lg:grid-cols-3">
      <SectionCard class="lg:col-span-2" title="Timeline">
        <SkeletonLoader v-if="loading" :rows="4" />
        <div v-else class="space-y-3">
          <div v-for="it in items" :key="`${it.type}-${it.ref_id}`" class="card p-4">
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <p class="text-sm font-semibold text-slate-900">{{ it.title }}</p>
                <p class="mt-0.5 text-xs text-slate-500">{{ formatDateTime(it.occurred_at) }}</p>
                <p v-if="it.summary" class="mt-2 text-sm text-slate-700">{{ it.summary }}</p>
              </div>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] font-semibold text-slate-600">
                {{ it.type }}
              </span>
            </div>
          </div>
          <div v-if="!items.length" class="p-6 text-center text-sm text-slate-500">No timeline items yet.</div>
        </div>
      </SectionCard>

      <SectionCard title="Quick links">
        <div class="space-y-2">
          <router-link to="/patient/history" class="btn-secondary w-full justify-center">Treatment history</router-link>
          <router-link to="/patient/vitals" class="btn-secondary w-full justify-center">Vitals</router-link>
          <router-link to="/patient/lab-results" class="btn-secondary w-full justify-center">Lab results</router-link>
          <router-link to="/patient/billing" class="btn-secondary w-full justify-center">Billing</router-link>
        </div>
      </SectionCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { store } from '@/store'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const loading = ref(true)
const items = ref([])

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  const me = store.user
  if (!me?.id) {
    loading.value = false
    return
  }
  // Patient model id is not the same as user id; we need patient_id.
  // For now, use v1 /patient/profile to get patient.id, then v2 timeline.
  const prof = await api.get('/patient/profile')
  const patientId = prof.data?.id
  const { data } = await api.get(`/v2/ehr/patients/${patientId}/timeline`, { params: { limit: 100 } })
  items.value = data.items || []
  loading.value = false
})
</script>

