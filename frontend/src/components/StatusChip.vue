<template>
  <span :class="chipClass" class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize">
    {{ label }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: String, required: true },
  label: { type: String, default: '' },
})

const chipClass = computed(() => {
  const map = {
    pending: 'bg-warning-50 text-warning-600 ring-1 ring-warning-500/20',
    confirmed: 'bg-primary-50 text-primary-600 ring-1 ring-primary-500/20',
    completed: 'bg-success-50 text-success-600 ring-1 ring-success-500/20',
    cancelled: 'bg-danger-50 text-danger-600 ring-1 ring-danger-500/20',
    no_show: 'bg-slate-100 text-slate-600 ring-1 ring-slate-300',
    active: 'bg-success-50 text-success-600 ring-1 ring-success-500/20',
    blocked: 'bg-danger-50 text-danger-600 ring-1 ring-danger-500/20',
  }
  return map[props.status?.toLowerCase()] || 'bg-slate-100 text-slate-600 ring-1 ring-slate-200'
})
</script>
