<template>
  <SectionCard title="Two-factor authentication (MFA)">
    <div class="space-y-3">
      <p class="text-sm text-slate-600">
        Add an extra layer of security using an authenticator app (TOTP).
      </p>

      <div v-if="setupUri" class="rounded-xl border border-slate-200 bg-slate-50 p-4">
        <p class="text-xs font-semibold uppercase text-slate-500">Setup URI</p>
        <p class="mt-1 break-all text-xs text-slate-700">{{ setupUri }}</p>
        <p class="mt-2 text-xs text-slate-500">
          Paste this into an authenticator app that supports manual entry, or generate a QR from it externally.
        </p>
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label-text">Verification code</label>
          <input v-model="code" class="input-field" inputmode="numeric" placeholder="6-digit code" />
        </div>
        <div class="flex items-end gap-2">
          <button class="btn-secondary btn-sm" :disabled="loading" @click="startSetup">
            {{ loading ? 'Working…' : 'Start setup' }}
          </button>
          <button class="btn-primary btn-sm" :disabled="loading || !setupUri || !code.trim()" @click="verify">
            Enable
          </button>
        </div>
      </div>
    </div>
  </SectionCard>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import SectionCard from '@/components/SectionCard.vue'

const toast = useToast()
const loading = ref(false)
const setupUri = ref('')
const code = ref('')

async function startSetup() {
  loading.value = true
  try {
    const { data } = await api.post('/v2/auth/mfa/setup')
    setupUri.value = data.otpauth_uri
    toast.success('MFA setup started')
  } catch (e) {
    toast.error(e.response?.data?.msg || 'MFA setup failed')
  } finally {
    loading.value = false
  }
}

async function verify() {
  loading.value = true
  try {
    await api.post('/v2/auth/mfa/verify', { code: code.value })
    toast.success('MFA enabled')
    code.value = ''
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Verification failed')
  } finally {
    loading.value = false
  }
}
</script>

