<template>
  <div class="flex h-screen overflow-hidden bg-slate-50">
    <!-- Mobile sidebar overlay -->
    <Transition name="fade">
      <div
        v-if="store.sidebarOpen"
        class="fixed inset-0 z-40 bg-slate-900/50 lg:hidden"
        @click="store.sidebarOpen = false"
      />
    </Transition>

    <!-- Sidebar -->
    <aside
      :class="store.sidebarOpen ? 'translate-x-0' : '-translate-x-full'"
      class="fixed inset-y-0 left-0 z-50 flex w-64 flex-col bg-[var(--color-sidebar)] transition-transform duration-200 lg:static lg:translate-x-0"
    >
      <!-- Brand -->
      <div class="flex h-16 items-center gap-3 px-5">
        <div class="flex h-9 w-9 items-center justify-center rounded-xl bg-primary-600">
          <Heart class="h-5 w-5 text-white" />
        </div>
        <div>
          <span class="text-base font-bold text-white">MedFlow</span>
          <span class="ml-1 text-xs font-medium text-primary-300">HMS</span>
        </div>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 space-y-1 overflow-y-auto px-3 py-4">
        <div v-for="group in navGroups" :key="group.label" class="mb-4">
          <p class="mb-2 px-3 text-[10px] font-bold uppercase tracking-widest text-slate-500">
            {{ group.label }}
          </p>
          <router-link
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            @click="store.sidebarOpen = false"
            :class="isActive(item.to) ? 'bg-[var(--color-sidebar-active)] text-white' : 'text-slate-300 hover:bg-[var(--color-sidebar-hover)] hover:text-white'"
            class="flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition"
          >
            <component :is="item.icon" class="h-5 w-5 shrink-0" />
            {{ item.label }}
          </router-link>
        </div>
      </nav>

      <!-- User section at bottom -->
      <div class="border-t border-white/10 p-4">
        <div class="flex items-center gap-3">
          <div class="flex h-9 w-9 items-center justify-center rounded-full bg-primary-700 text-sm font-bold text-white">
            {{ initials }}
          </div>
          <div class="min-w-0 flex-1">
            <p class="truncate text-sm font-medium text-white">
              {{ store.role === 'doctor' ? 'Dr. ' : '' }}{{ store.user?.username }}
            </p>
            <p class="truncate text-xs capitalize text-slate-400">{{ store.role }}</p>
          </div>
          <button @click="logout" class="rounded-lg p-1.5 text-slate-400 transition hover:bg-white/10 hover:text-white" title="Logout">
            <LogOut class="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main content -->
    <div class="flex flex-1 flex-col overflow-hidden">
      <!-- Topbar -->
      <header class="flex h-16 shrink-0 items-center gap-4 border-b border-slate-200 bg-white px-4 lg:px-6">
        <button @click="store.toggleSidebar()" class="btn-icon lg:hidden">
          <Menu class="h-5 w-5" />
        </button>
        <div class="flex-1" />
        <div class="relative flex items-center gap-3">
          <span class="hidden text-sm text-slate-500 sm:block">
            {{ greeting }}, <span class="font-semibold text-slate-700">{{ store.user?.username }}</span>
          </span>
          <button class="btn-icon relative" @click="toggleNotif" title="Notifications">
            <Bell class="h-5 w-5" />
            <span
              v-if="store.unreadCount"
              class="absolute -right-1 -top-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-danger-600 px-1 text-[10px] font-bold text-white"
            >
              {{ store.unreadCount > 99 ? '99+' : store.unreadCount }}
            </span>
          </button>
        </div>

        <div
          v-if="notifOpen"
          class="absolute right-4 top-16 z-30 w-[360px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl"
        >
          <div class="flex items-center justify-between border-b border-slate-200 px-4 py-3">
            <p class="text-sm font-semibold text-slate-900">Notifications</p>
            <button class="btn-ghost btn-sm text-slate-500" @click="markAllRead" :disabled="!store.unreadCount">Mark all read</button>
          </div>
          <div class="max-h-[420px] overflow-y-auto">
            <button
              v-for="n in store.notifications"
              :key="n.id"
              class="w-full px-4 py-3 text-left hover:bg-slate-50"
              @click="openNotification(n)"
            >
              <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                  <p class="truncate text-sm font-semibold" :class="n.is_read ? 'text-slate-700' : 'text-slate-900'">
                    {{ n.title }}
                  </p>
                  <p class="mt-0.5 line-clamp-2 text-xs text-slate-500">{{ n.message }}</p>
                  <p class="mt-1 text-[11px] text-slate-400">{{ formatDateTime(n.created_at) }}</p>
                </div>
                <span v-if="!n.is_read" class="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary-600" />
              </div>
            </button>
            <div v-if="!store.notifications.length" class="p-6 text-center text-sm text-slate-500">No notifications</div>
          </div>
        </div>
      </header>

      <!-- Page content -->
      <main class="flex-1 overflow-y-auto p-4 lg:p-6">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { store } from '@/store'
import {
  Heart, Menu, LogOut,
  LayoutDashboard, Users, UserCog, CalendarDays,
  Clock, Stethoscope, ClipboardList,
  Building2, UserCircle, FileText, Pill, Activity, Receipt, Bell,
  Package, ShoppingCart,
} from 'lucide-vue-next'
import api from '@/api'

const router = useRouter()
const route = useRoute()

const initials = computed(() => {
  const name = store.user?.username || ''
  return name.charAt(0).toUpperCase()
})

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return 'Good morning'
  if (h < 17) return 'Good afternoon'
  return 'Good evening'
})

const navConfig = {
  admin: [
    {
      label: 'Overview',
      items: [
        { to: '/admin', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      label: 'Management',
      items: [
        { to: '/admin/doctors', label: 'Doctors', icon: Stethoscope },
        { to: '/admin/patients', label: 'Patients', icon: Users },
        { to: '/admin/appointments', label: 'Appointments', icon: CalendarDays },
        { to: '/admin/departments', label: 'Departments', icon: Building2 },
        { to: '/admin/medications', label: 'Medications', icon: Pill },
        { to: '/admin/lab-tests', label: 'Lab Tests', icon: ClipboardList },
        { to: '/admin/billing', label: 'Billing', icon: Receipt },
        { to: '/admin/inventory', label: 'Inventory', icon: Package },
        { to: '/admin/analytics', label: 'Analytics', icon: Activity },
        { to: '/admin/audit-log', label: 'Audit Log', icon: ClipboardList },
      ],
    },
    {
      label: 'Account',
      items: [
        { to: '/admin/profile', label: 'Profile', icon: UserCircle },
      ],
    },
  ],
  doctor: [
    {
      label: 'Overview',
      items: [
        { to: '/doctor', label: 'Dashboard', icon: LayoutDashboard },
      ],
    },
    {
      label: 'Schedule',
      items: [
        { to: '/doctor/availability', label: 'Availability', icon: Clock },
      ],
    },
    {
      label: 'Account',
      items: [
        { to: '/doctor/profile', label: 'Profile', icon: UserCircle },
      ],
    },
  ],
  patient: [
    {
      label: 'Overview',
      items: [
        { to: '/patient', label: 'Dashboard', icon: LayoutDashboard },
        { to: '/patient/health', label: 'Health', icon: Activity },
      ],
    },
    {
      label: 'Healthcare',
      items: [
        { to: '/patient/departments', label: 'Departments', icon: Building2 },
        { to: '/patient/history', label: 'Treatment History', icon: FileText },
        { to: '/patient/vitals', label: 'Vitals History', icon: Activity },
        { to: '/patient/trends', label: 'Health Trends', icon: Activity },
        { to: '/patient/lab-results', label: 'Lab Results', icon: ClipboardList },
        { to: '/patient/prescriptions', label: 'Prescriptions', icon: ShoppingCart },
        { to: '/patient/documents', label: 'Documents', icon: FileText },
        { to: '/patient/billing', label: 'Bills & Payments', icon: Receipt },
      ],
    },
    {
      label: 'Account',
      items: [
        { to: '/patient/profile', label: 'Profile', icon: UserCircle },
      ],
    },
  ],
}

const navGroups = computed(() => navConfig[store.role] || [])

function isActive(path) {
  if (path === `/${store.role}`) return route.path === path
  return route.path.startsWith(path)
}

function logout() {
  store.logout()
  router.push('/login')
}

const notifOpen = ref(false)
let _notifTimer = null

function formatDateTime(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

async function fetchNotifications() {
  if (!store.isLoggedIn) return
  const { data } = await api.get('/notifications')
  store.notifications = data.items || []
  store.unreadCount = data.unread_count || 0
}

function toggleNotif() {
  notifOpen.value = !notifOpen.value
  if (notifOpen.value) fetchNotifications()
}

async function markAllRead() {
  await api.put('/notifications/read-all')
  await fetchNotifications()
}

async function openNotification(n) {
  try {
    if (!n.is_read) await api.put(`/notifications/${n.id}/read`)
  } catch {}
  notifOpen.value = false
  await fetchNotifications()
  if (n.link) router.push(n.link)
}

onMounted(() => {
  fetchNotifications()
  _notifTimer = setInterval(fetchNotifications, 30000)
})

onBeforeUnmount(() => {
  if (_notifTimer) clearInterval(_notifTimer)
})
</script>
