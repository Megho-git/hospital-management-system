<template>
  <div>
    <PageHeader title="Telemedicine Room" subtitle="Secure video consultation" />

    <SectionCard title="Connection" class="mb-6">
      <div class="flex flex-wrap items-center gap-2">
        <button class="btn-primary btn-sm" :disabled="connecting || connected" @click="join">
          {{ connected ? 'Connected' : (connecting ? 'Connecting…' : 'Join call') }}
        </button>
        <button class="btn-secondary btn-sm" :disabled="!connected" @click="leave">Leave</button>
        <span v-if="statusMsg" class="text-sm text-slate-600">{{ statusMsg }}</span>
      </div>
      <p v-if="notConfigured" class="mt-3 text-sm text-slate-600">
        Telemedicine is not configured on the server yet (Twilio credentials missing).
      </p>
    </SectionCard>

    <div class="grid gap-6 lg:grid-cols-3">
      <SectionCard title="Local" class="lg:col-span-1">
        <div ref="localEl" class="min-h-[240px] rounded-xl bg-slate-950/90" />
      </SectionCard>
      <SectionCard title="Remote" class="lg:col-span-1">
        <div ref="remoteEl" class="min-h-[240px] rounded-xl bg-slate-950/90" />
      </SectionCard>
      <SectionCard title="Chat" class="lg:col-span-1" :noPadding="true">
        <div class="flex h-[240px] flex-col">
          <div class="flex-1 space-y-2 overflow-y-auto p-4">
            <div v-for="m in messages" :key="m.id" class="text-sm">
              <p class="text-xs text-slate-500">
                <span class="font-semibold text-slate-700">{{ m.sender_name || 'User' }}</span>
                · {{ formatChatTime(m.created_at) }}
              </p>
              <p class="text-slate-800">{{ m.body }}</p>
            </div>
            <p v-if="!messages.length" class="text-sm text-slate-500">No messages yet.</p>
          </div>
          <div class="border-t border-slate-200 p-3">
            <form class="flex gap-2" @submit.prevent="send">
              <input v-model="draft" class="input-field" placeholder="Type a message…" />
              <button class="btn-primary btn-sm" :disabled="sending || !draft.trim()">Send</button>
            </form>
          </div>
        </div>
      </SectionCard>
    </div>
  </div>
</template>

<script setup>
import { ref, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import api from '@/api'
import PageHeader from '@/components/PageHeader.vue'
import SectionCard from '@/components/SectionCard.vue'

import Video from 'twilio-video'

const route = useRoute()
const appointmentId = route.params.id

const connecting = ref(false)
const connected = ref(false)
const notConfigured = ref(false)
const statusMsg = ref('')

const localEl = ref(null)
const remoteEl = ref(null)

let room = null

const conversationId = ref(null)
const messages = ref([])
const draft = ref('')
const sending = ref(false)
let pollTimer = null

function formatChatTime(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' })
}

function clearNode(el) {
  if (!el) return
  while (el.firstChild) el.removeChild(el.firstChild)
}

function attachTrack(container, track) {
  const node = track.attach()
  node.style.width = '100%'
  node.style.height = '100%'
  node.style.objectFit = 'cover'
  container.appendChild(node)
}

function detachParticipant(participant, container) {
  participant.tracks.forEach(publication => {
    const track = publication.track
    if (track) {
      track.detach().forEach(el => el.remove())
    }
  })
  clearNode(container)
}

async function join() {
  connecting.value = true
  statusMsg.value = ''
  notConfigured.value = false
  try {
    const { data } = await api.post(`/v2/telemedicine/appointments/${appointmentId}/token`)
    const token = data.token
    const roomName = data.room
    statusMsg.value = `Joining ${roomName}…`

    room = await Video.connect(token, { name: roomName, audio: true, video: { width: 640 } })
    connected.value = true
    statusMsg.value = 'Connected'

    // Local participant tracks
    clearNode(localEl.value)
    room.localParticipant.tracks.forEach(pub => {
      if (pub.track) attachTrack(localEl.value, pub.track)
    })

    // Existing participants
    room.participants.forEach(p => {
      p.tracks.forEach(pub => {
        if (pub.track) attachTrack(remoteEl.value, pub.track)
      })
      p.on('trackSubscribed', track => attachTrack(remoteEl.value, track))
      p.on('disconnected', () => detachParticipant(p, remoteEl.value))
    })

    room.on('participantConnected', p => {
      p.on('trackSubscribed', track => attachTrack(remoteEl.value, track))
    })
    room.on('participantDisconnected', p => detachParticipant(p, remoteEl.value))
  } catch (e) {
    const msg = e.response?.data?.msg || e.message || 'Failed to join'
    if (e.response?.status === 501) notConfigured.value = true
    statusMsg.value = msg
  } finally {
    connecting.value = false
  }
}

async function initMessaging() {
  const { data } = await api.get(`/v2/messaging/appointments/${appointmentId}/conversation`)
  conversationId.value = data.id
  await fetchMessages()
  pollTimer = setInterval(fetchMessages, 2500)
}

async function fetchMessages() {
  if (!conversationId.value) return
  const lastId = messages.value.length ? messages.value[messages.value.length - 1].id : null
  const { data } = await api.get(`/v2/messaging/conversations/${conversationId.value}/messages`, { params: { after_id: lastId, limit: 200 } })
  const incoming = data.items || []
  if (incoming.length) messages.value = [...messages.value, ...incoming]
}

async function send() {
  if (!conversationId.value) return
  sending.value = true
  try {
    const body = draft.value.trim()
    if (!body) return
    await api.post(`/v2/messaging/conversations/${conversationId.value}/messages`, { body })
    draft.value = ''
    await fetchMessages()
  } finally {
    sending.value = false
  }
}

function leave() {
  try {
    if (room) room.disconnect()
  } catch {}
  room = null
  connected.value = false
  statusMsg.value = 'Disconnected'
  clearNode(localEl.value)
  clearNode(remoteEl.value)
}

onMounted(() => initMessaging())

onBeforeUnmount(() => {
  if (pollTimer) clearInterval(pollTimer)
  leave()
})
</script>

