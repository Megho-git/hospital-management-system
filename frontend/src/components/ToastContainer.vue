<template>
  <div class="fixed top-4 right-4 z-50 flex flex-col gap-2 w-80">
    <TransitionGroup name="toast">
      <div
        v-for="t in store.toasts"
        :key="t.id"
        :class="toastClass(t.type)"
        class="flex items-start gap-3 rounded-lg border p-3.5 shadow-lg backdrop-blur-sm"
      >
        <component :is="toastIcon(t.type)" class="mt-0.5 h-5 w-5 shrink-0" />
        <p class="flex-1 text-sm font-medium leading-snug">{{ t.message }}</p>
        <button @click="store.removeToast(t.id)" class="shrink-0 opacity-60 hover:opacity-100">
          <X class="h-4 w-4" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { store } from '@/store'
import { CheckCircle, AlertTriangle, XCircle, Info, X } from 'lucide-vue-next'

const icons = { success: CheckCircle, error: XCircle, warning: AlertTriangle, info: Info }
const toastIcon = (type) => icons[type] || Info

function toastClass(type) {
  const map = {
    success: 'border-success-500/30 bg-success-50/95 text-success-700',
    error: 'border-danger-500/30 bg-danger-50/95 text-danger-700',
    warning: 'border-warning-500/30 bg-warning-50/95 text-warning-600',
    info: 'border-primary-500/30 bg-primary-50/95 text-primary-700',
  }
  return map[type] || map.info
}
</script>

<style scoped>
.toast-enter-active { animation: slideIn 0.25s ease-out; }
.toast-leave-active { animation: slideOut 0.2s ease-in; }
.toast-move { transition: transform 0.25s ease; }
@keyframes slideIn { from { opacity: 0; transform: translateX(100%); } to { opacity: 1; transform: translateX(0); } }
@keyframes slideOut { from { opacity: 1; transform: translateX(0); } to { opacity: 0; transform: translateX(100%); } }
</style>
