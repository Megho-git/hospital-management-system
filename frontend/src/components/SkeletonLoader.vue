<template>
  <div class="animate-pulse space-y-3">
    <div v-for="i in rows" :key="i" class="flex gap-4">
      <div v-if="avatar" class="h-10 w-10 rounded-full bg-slate-200" />
      <div class="flex-1 space-y-2 py-1">
        <div class="h-3 rounded-full bg-slate-200" :style="{ width: randomWidth() }" />
        <div class="h-3 rounded-full bg-slate-200" :style="{ width: randomWidth() }" />
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  rows: { type: Number, default: 4 },
  avatar: { type: Boolean, default: false },
})

function randomWidth() {
  return `${55 + Math.random() * 40}%`
}
</script>
