<template>
  <div class="card overflow-hidden">
    <div v-if="title || $slots.header" class="flex items-center justify-between border-b border-slate-100 px-5 py-3.5">
      <h3 v-if="title" class="text-sm font-semibold text-slate-800">{{ title }}</h3>
      <slot name="header" />
    </div>
    <div :class="noPadding ? '' : 'p-5'">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' },
  noPadding: { type: Boolean, default: false },
})
</script>
