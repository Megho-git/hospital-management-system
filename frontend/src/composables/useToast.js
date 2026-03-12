import { store } from '@/store'

export function useToast() {
  return {
    success: (msg) => store.addToast('success', msg),
    error: (msg) => store.addToast('error', msg),
    warning: (msg) => store.addToast('warning', msg),
    info: (msg) => store.addToast('info', msg),
  }
}
