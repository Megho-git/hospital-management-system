<template>
  <div class="card flex items-center gap-4 p-5">
    <div :class="iconBg" class="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl">
      <component :is="icon" class="h-6 w-6" :class="iconColor" />
    </div>
    <div class="min-w-0">
      <p class="text-2xl font-bold text-slate-900">{{ value }}</p>
      <p class="truncate text-sm text-slate-500">{{ label }}</p>
    </div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: Object, required: true },
  iconBg: { type: String, default: 'bg-primary-50' },
  iconColor: { type: String, default: 'text-primary-600' },
})
</script>
