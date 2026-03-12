<template>
  <div>
    <PageHeader :title="doctor ? `Dr. ${doctor.username}` : 'Doctor Profile'" subtitle="View profile and book an appointment">
      <template #actions>
        <router-link to="/patient/departments" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back
        </router-link>
      </template>
    </PageHeader>

    <SkeletonLoader v-if="!doctor" :rows="4" />
    <template v-else>
      <!-- Doctor Info Card -->
      <SectionCard class="mb-6">
        <div class="flex flex-col gap-6 sm:flex-row">
          <div class="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-primary-500 to-accent-500 text-2xl font-bold text-white">
            {{ doctor.username.charAt(0).toUpperCase() }}
          </div>
          <div class="grid flex-1 grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            <InfoItem label="Department" :value="doctor.department || 'N/A'" />
            <InfoItem label="Specialization" :value="doctor.specialization || 'N/A'" />
            <InfoItem label="Qualification" :value="doctor.qualification || 'N/A'" />
            <InfoItem label="Experience" :value="`${doctor.experience_years} years`" />
            <InfoItem label="Phone" :value="doctor.phone || 'N/A'" />
          </div>
        </div>
      </SectionCard>

      <!-- Availability -->
      <SectionCard title="Available Slots">
        <div v-if="availability.length" class="space-y-2">
          <div
            v-for="a in availability"
            :key="a.id"
            class="flex items-center justify-between rounded-lg border border-slate-100 p-3 transition hover:border-primary-200 hover:bg-primary-50/30"
          >
            <div class="flex items-center gap-3">
              <CalendarDays class="h-5 w-5 text-primary-500" />
              <div>
                <p class="font-medium text-slate-900">{{ formatDate(a.date) }}</p>
                <p class="text-sm text-slate-500">{{ a.start_time }} - {{ a.end_time }}</p>
              </div>
            </div>
            <router-link
              :to="`/patient/book/${doctor.id}?date=${a.date}&start=${a.start_time}&end=${a.end_time}`"
              class="btn-primary btn-sm"
            >
              Book Slot
            </router-link>
          </div>
        </div>
        <EmptyState
          v-else
          title="No availability"
          message="This doctor hasn't set any available time slots yet."
          :icon="CalendarX2"
        />
      </SectionCard>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, h } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { ArrowLeft, CalendarDays, CalendarX2 } from 'lucide-vue-next'

const InfoItem = (props) => h('div', [
  h('p', { class: 'text-xs font-medium text-slate-400 uppercase tracking-wide' }, props.label),
  h('p', { class: 'mt-0.5 text-sm font-semibold text-slate-800' }, props.value),
])
InfoItem.props = { label: String, value: String }

const route = useRoute()
const doctor = ref(null)
const availability = ref([])

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

onMounted(async () => {
  const { data } = await api.get(`/patient/doctors/${route.params.id}`)
  doctor.value = data.doctor
  availability.value = data.availability
})
</script>
