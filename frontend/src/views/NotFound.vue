<template>
  <div class="mx-auto max-w-xl">
    <div class="card p-8 text-center">
      <h1 class="text-2xl font-bold text-slate-900">Page not found</h1>
      <p class="mt-2 text-sm text-slate-500">The page you’re looking for doesn’t exist or has moved.</p>
      <div class="mt-6 flex justify-center gap-2">
        <router-link to="/" class="btn-primary">Go to login</router-link>
        <button class="btn-secondary" @click="goBack">Go back</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()
function goBack() {
  if (window.history.length > 1) window.history.back()
  else router.push('/')
}
</script>

