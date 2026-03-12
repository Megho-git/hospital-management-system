<template>
  <div class="flex flex-col items-center justify-center py-12 text-center">
    <div class="mb-4 rounded-full bg-slate-100 p-4">
      <component :is="icon" class="h-8 w-8 text-slate-400" />
    </div>
    <h3 class="text-sm font-semibold text-slate-800">{{ title }}</h3>
    <p class="mt-1 max-w-sm text-sm text-slate-500">{{ message }}</p>
    <div v-if="$slots.action" class="mt-4">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
import { Inbox } from 'lucide-vue-next'

defineProps({
  title: { type: String, default: 'No data' },
  message: { type: String, default: 'There are no records to display.' },
  icon: { type: Object, default: () => Inbox },
})
</script>
