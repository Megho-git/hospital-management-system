<template>
  <Teleport to="body">
    <Transition name="fade">
      <div v-if="modelValue" class="fixed inset-0 z-50 flex items-center justify-center p-4">
        <div class="fixed inset-0 bg-slate-900/50 backdrop-blur-sm" @click="cancel" />
        <div class="relative w-full max-w-md rounded-2xl bg-white p-6 shadow-xl">
          <div class="mb-4 flex items-start gap-3">
            <div :class="iconBg" class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full">
              <component :is="iconComp" class="h-5 w-5" :class="iconColor" />
            </div>
            <div>
              <h3 class="text-base font-semibold text-slate-900">{{ title }}</h3>
              <p class="mt-1 text-sm text-slate-500">{{ message }}</p>
            </div>
          </div>
          <div class="flex justify-end gap-2">
            <button @click="cancel" class="btn-secondary btn-sm">Cancel</button>
            <button @click="confirm" :class="confirmClass">{{ confirmText }}</button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'
import { AlertTriangle, Trash2, Info } from 'lucide-vue-next'

const props = defineProps({
  modelValue: Boolean,
  title: { type: String, default: 'Confirm action' },
  message: { type: String, default: 'Are you sure you want to proceed?' },
  confirmText: { type: String, default: 'Confirm' },
  variant: { type: String, default: 'danger' },
})

const emit = defineEmits(['update:modelValue', 'confirm'])

const iconComp = computed(() => props.variant === 'danger' ? Trash2 : props.variant === 'warning' ? AlertTriangle : Info)
const iconBg = computed(() => props.variant === 'danger' ? 'bg-danger-50' : props.variant === 'warning' ? 'bg-warning-50' : 'bg-primary-50')
const iconColor = computed(() => props.variant === 'danger' ? 'text-danger-600' : props.variant === 'warning' ? 'text-warning-600' : 'text-primary-600')
const confirmClass = computed(() => props.variant === 'danger' ? 'btn-danger btn-sm' : 'btn-primary btn-sm')

function cancel() { emit('update:modelValue', false) }
function confirm() { emit('confirm'); emit('update:modelValue', false) }
</script>
