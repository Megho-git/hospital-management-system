<template>
  <div>
    <PageHeader title="My Profile" subtitle="Manage your professional information" />

    <SectionCard title="Doctor Information">
      <SkeletonLoader v-if="!profile" :rows="3" />
      <form v-else @submit.prevent="save" class="space-y-5">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div>
            <label class="label-text">Username</label>
            <input :value="profile.username" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Email</label>
            <input :value="profile.email" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Last login</label>
            <input :value="formatDateTime(profile.last_login_at)" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Department</label>
            <input :value="profile.department" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Specialization</label>
            <input v-model="profile.specialization" class="input-field" />
          </div>
          <div>
            <label class="label-text">Qualification</label>
            <input v-model="profile.qualification" class="input-field" />
          </div>
          <div>
            <label class="label-text">Experience (years)</label>
            <input v-model.number="profile.experience_years" type="number" class="input-field" min="0" />
          </div>
          <div>
            <label class="label-text">Phone</label>
            <input v-model="profile.phone" class="input-field" />
          </div>
        </div>
        <button type="submit" class="btn-primary">Save Changes</button>
      </form>
    </SectionCard>

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
import MfaSetupCard from '@/components/MfaSetupCard.vue'

const toast = useToast()
const profile = ref(null)

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function save() {
  await api.put('/doctor/profile', profile.value)
  toast.success('Profile updated successfully')
}

onMounted(async () => {
  const { data } = await api.get('/doctor/profile')
  profile.value = data
})
</script>
