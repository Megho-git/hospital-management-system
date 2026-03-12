<template>
  <div>
    <PageHeader title="Medical Documents" subtitle="Upload and download your medical files" />

    <SectionCard title="Upload">
      <div class="grid gap-3 sm:grid-cols-3">
        <div class="sm:col-span-1">
          <label class="label-text">Category</label>
          <select v-model="form.category" class="input-field">
            <option value="medical">Medical</option>
            <option value="lab_report">Lab report</option>
            <option value="imaging">Imaging</option>
            <option value="discharge">Discharge</option>
            <option value="prescription">Prescription</option>
          </select>
        </div>
        <div class="sm:col-span-2">
          <label class="label-text">Title (optional)</label>
          <input v-model="form.title" class="input-field" placeholder="e.g., Blood test report (Jan 2026)" />
        </div>
        <div class="sm:col-span-3">
          <label class="label-text">File</label>
          <input type="file" class="input-field" @change="onPickFile" />
        </div>
      </div>
      <div class="mt-3 flex gap-2">
        <button class="btn-primary btn-sm" :disabled="uploading || !pickedFile" @click="upload">
          {{ uploading ? 'Uploading…' : 'Upload' }}
        </button>
        <button class="btn-secondary btn-sm" :disabled="uploading" @click="refresh">Refresh list</button>
      </div>
    </SectionCard>

    <SectionCard title="My documents" class="mt-6">
      <SkeletonLoader v-if="loading" :rows="4" />
      <div v-else class="space-y-2">
        <div v-for="d in docs" :key="d.id" class="card flex items-start justify-between gap-3 p-4">
          <div class="min-w-0">
            <p class="truncate text-sm font-semibold text-slate-900">{{ d.title || d.original_filename || `Document #${d.id}` }}</p>
            <p class="mt-0.5 text-xs text-slate-500">
              {{ d.category }} · {{ formatBytes(d.size_bytes) }} · {{ formatDateTime(d.created_at) }}
            </p>
          </div>
          <button class="btn-secondary btn-sm" @click="download(d)">Download</button>
        </div>
        <div v-if="!docs.length" class="p-6 text-center text-sm text-slate-500">No documents uploaded yet.</div>
      </div>
    </SectionCard>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import api from '@/api'
import { useToast } from '@/composables/useToast'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'
import SkeletonLoader from '@/components/SkeletonLoader.vue'

const toast = useToast()
const loading = ref(true)
const uploading = ref(false)
const docs = ref([])

const form = reactive({ category: 'medical', title: '' })
const pickedFile = ref(null)
let patientId = null

function onPickFile(e) {
  pickedFile.value = e.target.files?.[0] || null
}

function formatDateTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
}

function formatBytes(n) {
  if (!n && n !== 0) return '—'
  const kb = 1024
  const mb = kb * 1024
  if (n >= mb) return `${(n / mb).toFixed(1)} MB`
  if (n >= kb) return `${(n / kb).toFixed(1)} KB`
  return `${n} B`
}

async function ensurePatientId() {
  if (patientId) return patientId
  const prof = await api.get('/patient/profile')
  patientId = prof.data?.id
  return patientId
}

async function refresh() {
  loading.value = true
  const pid = await ensurePatientId()
  const { data } = await api.get(`/v2/ehr/patients/${pid}/documents`)
  docs.value = data.items || []
  loading.value = false
}

async function upload() {
  const pid = await ensurePatientId()
  if (!pickedFile.value) return
  uploading.value = true
  try {
    const fd = new FormData()
    fd.append('file', pickedFile.value)
    fd.append('category', form.category)
    if (form.title.trim()) fd.append('title', form.title.trim())
    await api.post(`/v2/ehr/patients/${pid}/documents`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
    toast.success('Document uploaded')
    pickedFile.value = null
    form.title = ''
    await refresh()
  } catch (e) {
    toast.error(e.response?.data?.msg || 'Upload failed')
  } finally {
    uploading.value = false
  }
}

async function download(d) {
  try {
    const res = await api.get(`/v2/ehr/documents/${d.id}/download`)
    // local storage returns file directly; axios will treat it as JSON unless blob.
    // For simplicity: if API returns url, open it; otherwise, fallback to opening endpoint in new tab.
    if (res.data?.url) {
      window.open(res.data.url, '_blank', 'noopener')
    } else {
      window.open(`/api/v2/ehr/documents/${d.id}/download`, '_blank', 'noopener')
    }
  } catch {
    window.open(`/api/v2/ehr/documents/${d.id}/download`, '_blank', 'noopener')
  }
}

onMounted(refresh)
</script>

