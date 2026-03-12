<template>
  <ToastContainer />
  <component :is="layout">
    <router-view v-if="!store.isLoggedIn" />
  </component>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { store } from '@/store'
import ToastContainer from '@/components/ToastContainer.vue'
import AppLayout from '@/layouts/AppLayout.vue'

const route = useRoute()

const layout = computed(() => {
  if (route.meta?.guest || !store.isLoggedIn) return 'div'
  return AppLayout
})
</script>
