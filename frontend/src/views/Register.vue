<template>
  <div class="flex min-h-screen">
    <!-- Left: branding panel -->
    <div class="hidden w-1/2 flex-col justify-between bg-gradient-to-br from-primary-700 via-primary-800 to-sidebar p-12 lg:flex">
      <div class="flex items-center gap-3">
        <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur">
          <Heart class="h-5 w-5 text-white" />
        </div>
        <span class="text-xl font-bold text-white">MedFlow <span class="text-primary-300">HMS</span></span>
      </div>
      <div>
        <h2 class="text-4xl font-extrabold leading-tight text-white">
          Your health,<br /><span class="text-primary-300">our priority.</span>
        </h2>
        <p class="mt-4 max-w-md text-base text-primary-200">
          Create your patient account to book appointments, track treatments, and manage your healthcare journey.
        </p>
      </div>
      <p class="text-xs text-primary-400">&copy; {{ new Date().getFullYear() }} MedFlow HMS. All rights reserved.</p>
    </div>

    <!-- Right: register form -->
    <div class="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div class="w-full max-w-md">
        <div class="mb-8 flex items-center gap-3 lg:hidden">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600">
            <Heart class="h-5 w-5 text-white" />
          </div>
          <span class="text-xl font-bold text-slate-900">MedFlow <span class="text-primary-600">HMS</span></span>
        </div>

        <h1 class="text-2xl font-bold text-slate-900">Create your account</h1>
        <p class="mt-1 text-sm text-slate-500">Register as a new patient</p>

        <form @submit.prevent="register" class="mt-8 space-y-4">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label class="label-text">Username</label>
              <input v-model="form.username" class="input-field" placeholder="johndoe" required />
            </div>
            <div>
              <label class="label-text">Email</label>
              <input v-model="form.email" type="email" class="input-field" placeholder="john@example.com" required />
            </div>
            <div class="sm:col-span-2">
              <label class="label-text">Password</label>
              <input v-model="form.password" type="password" class="input-field" placeholder="Min. 8 chars, 1 letter + 1 number" required />
              <div class="mt-2 flex items-center gap-2">
                <div class="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-200">
                  <div :class="strengthBarClass" class="h-full transition-all" :style="{ width: `${strengthPercent}%` }" />
                </div>
                <span class="text-xs font-semibold" :class="strengthTextClass">{{ strengthLabel }}</span>
              </div>
              <p v-if="form.password && !passwordValid" class="mt-1 text-xs text-danger-600">
                Password must be at least 8 characters and include at least 1 letter and 1 number.
              </p>
            </div>
            <div>
              <label class="label-text">Phone</label>
              <input v-model="form.phone" class="input-field" placeholder="+91 98765 43210" required />
            </div>
            <div>
              <label class="label-text">Gender</label>
              <select v-model="form.gender" class="select-field" required>
                <option value="" disabled>Select gender</option>
                <option>Male</option>
                <option>Female</option>
                <option>Other</option>
              </select>
            </div>
            <div>
              <label class="label-text">Date of Birth</label>
              <input v-model="form.date_of_birth" type="date" class="input-field" required :max="today" />
            </div>
            <div>
              <label class="label-text">Blood Group</label>
              <select v-model="form.blood_group" class="select-field" required>
                <option value="" disabled>Select blood group</option>
                <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
              </select>
            </div>
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
            {{ loading ? 'Creating account...' : 'Create account' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-slate-500">
          Already have an account?
          <router-link to="/login" class="font-semibold text-primary-600 hover:text-primary-700">Sign in</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'
import { useToast } from '@/composables/useToast'
import { Heart, Loader2 } from 'lucide-vue-next'

const router = useRouter()
const toast = useToast()
const today = new Date().toISOString().slice(0, 10)
const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const form = reactive({
  username: '', email: '', password: '', role: 'patient',
  phone: '', gender: '', date_of_birth: '', blood_group: '',
})
const loading = ref(false)

const passwordValid = computed(() => {
  const p = form.password || ''
  if (p.length < 8) return false
  if (!/[A-Za-z]/.test(p)) return false
  if (!/[0-9]/.test(p)) return false
  return true
})

const strength = computed(() => {
  const p = form.password || ''
  let s = 0
  if (p.length >= 8) s++
  if (/[A-Za-z]/.test(p)) s++
  if (/[0-9]/.test(p)) s++
  if (/[^A-Za-z0-9]/.test(p)) s++
  return s
})

const strengthPercent = computed(() => Math.min(100, (strength.value / 4) * 100))
const strengthLabel = computed(() => (strength.value <= 1 ? 'Weak' : strength.value === 2 ? 'Fair' : strength.value === 3 ? 'Good' : 'Strong'))
const strengthBarClass = computed(() => (strength.value <= 1 ? 'bg-danger-500' : strength.value === 2 ? 'bg-warning-500' : strength.value === 3 ? 'bg-primary-600' : 'bg-success-600'))
const strengthTextClass = computed(() => (strength.value <= 1 ? 'text-danger-600' : strength.value === 2 ? 'text-warning-700' : strength.value === 3 ? 'text-primary-700' : 'text-success-700'))

async function register() {
  loading.value = true
  try {
    if (!passwordValid.value) {
      toast.error('Please choose a stronger password')
      return
    }
    const { data } = await api.post('/auth/register', form)
    store.login(data.token, data.refresh_token, data.user)
    toast.success('Account created successfully!')
    router.push('/' + data.user.role)
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Registration failed')
  } finally {
    loading.value = false
  }
}
</script>
