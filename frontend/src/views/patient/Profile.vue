<template>
  <div>
    <PageHeader title="My Profile" subtitle="Manage your personal information" />
    <p class="mb-4 text-xs text-slate-500">Last login: <span class="font-medium text-slate-700">{{ formatDateTime(store.user?.last_login_at) }}</span></p>

    <SectionCard title="Personal Information" class="mb-6">
      <SkeletonLoader v-if="!profile" :rows="3" />
      <form v-else @submit.prevent="save" class="space-y-5">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label class="label-text">Phone</label>
            <input v-model="profile.phone" class="input-field" placeholder="+91 98765 43210" />
          </div>
          <div>
            <label class="label-text">Gender</label>
            <select v-model="profile.gender" class="select-field">
              <option value="">Select</option>
              <option value="Male">Male</option>
              <option value="Female">Female</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label class="label-text">Blood Group</label>
            <select v-model="profile.blood_group" class="select-field">
              <option value="">Select</option>
              <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
            </select>
          </div>
          <div>
            <label class="label-text">Date of Birth</label>
            <input v-model="profile.date_of_birth" type="date" class="input-field" :max="today" />
          </div>
          <div class="sm:col-span-2">
            <label class="label-text">Address</label>
            <input v-model="profile.address" class="input-field" placeholder="Enter your address" />
          </div>
        </div>
        <button type="submit" class="btn-primary">Save Changes</button>
      </form>
    </SectionCard>

    <SectionCard title="Medical Info" class="mb-6">
      <SkeletonLoader v-if="!profile" :rows="3" />
      <form v-else @submit.prevent="save" class="space-y-5">
        <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <div>
            <label class="label-text">Allergies</label>
            <textarea v-model="profile.allergies" class="input-field" rows="3" placeholder="e.g. Penicillin, Peanuts, Dust" />
            <p class="mt-1 text-xs text-slate-500">Comma-separated works best (shown as tags across the app).</p>
          </div>
          <div>
            <label class="label-text">Chronic Conditions</label>
            <textarea v-model="profile.chronic_conditions" class="input-field" rows="3" placeholder="e.g. Diabetes Type 2, Hypertension" />
          </div>
        </div>
        <button type="submit" class="btn-primary">Save Medical Info</button>
      </form>
    </SectionCard>

    <div class="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Emergency Contact">
        <SkeletonLoader v-if="!profile" :rows="2" />
        <form v-else @submit.prevent="save" class="space-y-5">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="label-text">Contact Name</label>
              <input v-model="profile.emergency_contact_name" class="input-field" placeholder="Full name" />
            </div>
            <div>
              <label class="label-text">Contact Phone</label>
              <input v-model="profile.emergency_contact_phone" class="input-field" placeholder="+91 ..." />
            </div>
          </div>
          <button type="submit" class="btn-primary">Save Emergency Contact</button>
        </form>
      </SectionCard>

      <SectionCard title="Insurance & Body Metrics">
        <SkeletonLoader v-if="!profile" :rows="3" />
        <form v-else @submit.prevent="save" class="space-y-5">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="label-text">Insurance Provider</label>
              <input v-model="profile.insurance_provider" class="input-field" placeholder="e.g. Star Health" />
            </div>
            <div>
              <label class="label-text">Insurance ID</label>
              <input v-model="profile.insurance_id" class="input-field" placeholder="Policy / Member ID" />
            </div>
            <div>
              <label class="label-text">Height (cm)</label>
              <input v-model.number="profile.height_cm" type="number" step="0.1" class="input-field" placeholder="e.g. 170" />
            </div>
            <div>
              <label class="label-text">Weight (kg)</label>
              <input v-model.number="profile.weight_kg" type="number" step="0.1" class="input-field" placeholder="e.g. 65" />
            </div>
          </div>
          <button type="submit" class="btn-primary">Save Insurance & Metrics</button>
        </form>
      </SectionCard>
    </div>

    <div class="mt-6">
      <MfaSetupCard />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'
import { store } from '@/store'
import MfaSetupCard from '@/components/MfaSetupCard.vue'

const toast = useToast()
const today = new Date().toISOString().slice(0, 10)
const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const profile = ref(null)

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function save() {
  await api.put('/patient/profile', profile.value)
  toast.success('Profile updated successfully')
}

onMounted(async () => {
  const { data } = await api.get('/patient/profile')
  profile.value = data
})
</script>
