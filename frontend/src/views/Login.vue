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
          Healthcare<br />management,<br /><span class="text-primary-300">simplified.</span>
        </h2>
        <p class="mt-4 max-w-md text-base text-primary-200">
          Streamline appointments, treatments, and operations for your clinic or hospital with a modern, integrated platform.
        </p>
      </div>
      <p class="text-xs text-primary-400">&copy; {{ new Date().getFullYear() }} MedFlow HMS. All rights reserved.</p>
    </div>

    <!-- Right: login form -->
    <div class="flex flex-1 flex-col items-center justify-center px-6 py-12">
      <div class="w-full max-w-sm">
        <!-- Mobile brand -->
        <div class="mb-8 flex items-center gap-3 lg:hidden">
          <div class="flex h-10 w-10 items-center justify-center rounded-xl bg-primary-600">
            <Heart class="h-5 w-5 text-white" />
          </div>
          <span class="text-xl font-bold text-slate-900">MedFlow <span class="text-primary-600">HMS</span></span>
        </div>

        <h1 class="text-2xl font-bold text-slate-900">Welcome back</h1>
        <p class="mt-1 text-sm text-slate-500">Sign in to your account to continue</p>

        <form @submit.prevent="login" class="mt-8 space-y-5">
          <div>
            <label class="label-text">Username</label>
            <input v-model="form.username" type="text" class="input-field" placeholder="Enter your username" required />
          </div>
          <div>
            <label class="label-text">Password</label>
            <input v-model="form.password" type="password" class="input-field" placeholder="Enter your password" required />
          </div>
          <div v-if="mfaRequired">
            <label class="label-text">MFA Code</label>
            <input v-model="form.mfa_code" inputmode="numeric" class="input-field" placeholder="6-digit code" />
            <p class="mt-1 text-xs text-slate-500">Enter the code from your authenticator app.</p>
          </div>
          <button type="submit" class="btn-primary w-full" :disabled="loading">
            <Loader2 v-if="loading" class="h-4 w-4 animate-spin" />
            {{ loading ? 'Signing in...' : 'Sign in' }}
          </button>
        </form>

        <p class="mt-6 text-center text-sm text-slate-500">
          Don't have an account?
          <router-link to="/register" class="font-semibold text-primary-600 hover:text-primary-700">Register as patient</router-link>
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api'
import { store } from '@/store'
import { useToast } from '@/composables/useToast'
import { Heart, Loader2 } from 'lucide-vue-next'

const router = useRouter()
const toast = useToast()
const form = reactive({ username: '', password: '', mfa_code: '' })
const loading = ref(false)
const mfaRequired = ref(false)

async function login() {
  loading.value = true
  try {
    // Prefer v2 login (supports MFA). v1 remains available for backward compatibility.
    const { data } = await api.post('/v2/auth/login', form)
    if (data?.mfa_required) {
      mfaRequired.value = true
      toast.info('MFA code required')
      return
    }
    store.login(data.token, data.refresh_token, data.user)
    toast.success(`Welcome back, ${data.user.username}!`)
    router.push('/' + data.user.role)
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Login failed')
  } finally {
    loading.value = false
  }
}
</script>
