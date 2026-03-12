<template>
  <div>
    <PageHeader title="Patient EHR Timeline" subtitle="Unified view of encounters, labs, and vitals">
      <template #actions>
        <router-link :to="`/doctor/patients/${patientId}/history`" class="btn-secondary btn-sm">
          <FileText class="h-4 w-4" /> Treatment History
        </router-link>
        <router-link to="/doctor" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back
        </router-link>
      </template>
    </PageHeader>

    <SectionCard title="Timeline">
      <SkeletonLoader v-if="loading" :rows="4" />
      <div v-else class="space-y-3">
        <div
          v-for="it in items"
          :key="`${it.type}-${it.ref_id}`"
          class="card p-4"
        >
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
        <div v-if="!items.length" class="p-6 text-center text-sm text-slate-500">No timeline items found.</div>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { ArrowLeft, FileText } from 'lucide-vue-next'

const route = useRoute()
const patientId = computed(() => route.params.id)

const loading = ref(true)
const items = ref([])

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  const { data } = await api.get(`/v2/ehr/patients/${patientId.value}/timeline`, { params: { limit: 100 } })
  items.value = data.items || []
  loading.value = false
})
</script>

