<template>
  <div>
    <PageHeader title="Book Appointment" :subtitle="doctor ? `Schedule a visit with Dr. ${doctor.username}` : 'Loading...'">
      <template #actions>
        <router-link :to="`/patient/doctors/${doctorId}`" class="btn-secondary btn-sm">
          <ArrowLeft class="h-4 w-4" /> Back to Doctor
        </router-link>
      </template>
    </PageHeader>

    <div class="grid gap-6 lg:grid-cols-3">
      <!-- Date picker column -->
      <div>
        <SectionCard title="Select Date">
          <div class="space-y-1">
            <button
              v-for="av in availableDates"
              :key="av.date"
              @click="selectDate(av.date)"
              :class="selectedDate === av.date
                ? 'border-primary-500 bg-primary-50 ring-2 ring-primary-500/20'
                : 'border-slate-200 hover:border-primary-300 hover:bg-slate-50'"
              class="flex w-full items-center justify-between rounded-lg border p-3 text-left transition"
            >
              <div>
                <p class="text-sm font-semibold text-slate-900">{{ formatDate(av.date) }}</p>
                <p class="text-xs text-slate-500">{{ av.slots }} slot{{ av.slots !== 1 ? 's' : '' }} available</p>
              </div>
              <CalendarDays class="h-4 w-4 text-slate-400" />
            </button>
            <EmptyState
              v-if="!availableDates.length && !loadingDates"
              title="No availability"
              message="This doctor has no available dates. Please check back later."
              :icon="CalendarX2"
            />
            <SkeletonLoader v-if="loadingDates" :rows="3" />
          </div>
        </SectionCard>
      </div>

      <!-- Time slot picker column -->
      <div>
        <SectionCard :title="selectedDate ? `Slots for ${formatDate(selectedDate)}` : 'Select a date first'">
          <SkeletonLoader v-if="loadingSlots" :rows="4" />
          <div v-else-if="selectedDate && slots.length" class="grid grid-cols-2 gap-2">
            <button
              v-for="slot in slots"
              :key="slot.time"
              @click="slot.available && selectSlot(slot.time)"
              :disabled="!slot.available"
              :class="[
                selectedSlot === slot.time
                  ? 'border-primary-500 bg-primary-50 text-primary-700 ring-2 ring-primary-500/20'
                  : slot.available
                    ? 'border-slate-200 text-slate-700 hover:border-primary-300 hover:bg-slate-50'
                    : 'border-slate-100 bg-slate-50 text-slate-300 cursor-not-allowed line-through',
              ]"
              class="flex items-center justify-center rounded-lg border px-3 py-2.5 text-sm font-medium transition"
            >
              <Clock class="mr-1.5 h-3.5 w-3.5" />
              {{ slot.time }}
            </button>
          </div>
          <div v-else-if="selectedDate && !slots.length && !loadingSlots" class="py-6 text-center">
            <p class="text-sm text-slate-500">All slots are booked for this date.</p>
          </div>
          <div v-else class="py-6 text-center">
            <p class="text-sm text-slate-400">Pick a date to see available time slots.</p>
          </div>
        </SectionCard>
      </div>

      <!-- Booking form column -->
      <div>
        <SectionCard title="Confirm Booking">
          <form @submit.prevent="book" class="space-y-4">
            <div>
              <label class="label-text">Selected Date</label>
              <p class="input-field bg-slate-50">{{ selectedDate ? formatDate(selectedDate) : 'Not selected' }}</p>
            </div>
            <div>
              <label class="label-text">Selected Time</label>
              <p class="input-field bg-slate-50">{{ selectedSlot || 'Not selected' }}</p>
            </div>
            <div>
              <label class="label-text">Reason for visit</label>
              <textarea v-model="reason" class="input-field" rows="3" placeholder="Describe your symptoms or reason..." />
            </div>
            <button
              type="submit"
              class="btn-primary w-full"
              :disabled="!selectedDate || !selectedSlot || loading"
            >
              <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
              {{ loading ? 'Booking...' : 'Confirm Booking' }}
            </button>
          </form>
        </SectionCard>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import EmptyState from '@/components/EmptyState.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { ArrowLeft, CalendarDays, CalendarX2, Clock, Loader2 } from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const toast = useToast()
const doctorId = route.params.doctorId

const doctor = ref(null)
const availableDates = ref([])
const loadingDates = ref(true)
const selectedDate = ref(route.query.date || '')
const slots = ref([])
const loadingSlots = ref(false)
const selectedSlot = ref(route.query.start || '')
const reason = ref('')
const loading = ref(false)

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso + 'T00:00').toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' })
}

async function selectDate(d) {
  selectedDate.value = d
  selectedSlot.value = ''
  loadingSlots.value = true
  try {
    const { data } = await api.get(`/patient/doctors/${doctorId}/slots`, { params: { date: d } })
    slots.value = data
  } catch {
    slots.value = []
  } finally {
    loadingSlots.value = false
  }
}

function selectSlot(time) {
  selectedSlot.value = time
}

async function book() {
  if (!selectedDate.value || !selectedSlot.value) return
  loading.value = true
  try {
    await api.post('/patient/appointments', {
      doctor_id: parseInt(doctorId),
      date: selectedDate.value,
      time_slot: selectedSlot.value,
      reason: reason.value,
    })
    toast.success('Appointment booked successfully!')
    setTimeout(() => router.push('/patient'), 1000)
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Booking failed')
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  try {
    const { data } = await api.get(`/patient/doctors/${doctorId}`)
    doctor.value = data.doctor

    const dateSlotCounts = {}
    for (const av of data.availability) {
      if (!dateSlotCounts[av.date]) dateSlotCounts[av.date] = 0
      try {
        const start = new Date(`2000-01-01T${av.start_time}`)
        const end = new Date(`2000-01-01T${av.end_time}`)
        dateSlotCounts[av.date] += Math.floor((end - start) / (30 * 60 * 1000))
      } catch { dateSlotCounts[av.date] += 1 }
    }
    availableDates.value = Object.entries(dateSlotCounts)
      .map(([d, s]) => ({ date: d, slots: s }))
      .sort((a, b) => a.date.localeCompare(b.date))
  } finally {
    loadingDates.value = false
  }

  if (selectedDate.value) {
    selectDate(selectedDate.value)
  }
})
</script>
