<template>
  <div>
    <PageHeader title="Admin Profile" subtitle="Manage your account settings" />

    <div class="grid gap-6 lg:grid-cols-2">
      <SectionCard title="Account Information">
        <SkeletonLoader v-if="!profile" :rows="2" />
        <form v-else @submit.prevent="save" class="space-y-4">
          <div>
            <label class="label-text">Username</label>
            <input :value="profile.username" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Last login</label>
            <input :value="formatDateTime(profile.last_login_at)" class="input-field bg-slate-50" disabled />
          </div>
          <div>
            <label class="label-text">Email</label>
            <input v-model="profile.email" type="email" class="input-field" />
          </div>
          <button type="submit" class="btn-primary">Update Email</button>
        </form>
      </SectionCard>

      <SectionCard title="Change Password">
        <form @submit.prevent="save" class="space-y-4">
          <div>
            <label class="label-text">Current Password</label>
            <input v-model="currentPassword" type="password" class="input-field" placeholder="Enter current password" />
          </div>
          <div>
            <label class="label-text">New Password</label>
            <input v-model="newPassword" type="password" class="input-field" placeholder="Enter new password" />
          </div>
          <button type="submit" class="btn-primary" :disabled="!newPassword">Change Password</button>
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
import MfaSetupCard from '@/components/MfaSetupCard.vue'

const toast = useToast()
const profile = ref(null)
const currentPassword = ref('')
const newPassword = ref('')

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function save() {
  try {
    const payload = { email: profile.value.email }
    if (newPassword.value) {
      payload.current_password = currentPassword.value
      payload.new_password = newPassword.value
    }
    await api.put('/admin/profile', payload)
    currentPassword.value = ''
    newPassword.value = ''
    toast.success('Profile updated successfully')
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Update failed')
  }
}

onMounted(async () => {
  const { data } = await api.get('/admin/profile')
  profile.value = data
})
</script>
