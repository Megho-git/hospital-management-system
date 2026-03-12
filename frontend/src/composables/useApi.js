import { ref } from 'vue'
import api from '@/api'
import { useToast } from './useToast'

export function useApi() {
  const loading = ref(false)
  const toast = useToast()

  async function call(method, url, data = null, options = {}) {
    loading.value = true
    try {
      const config = { method, url, ...options }
      if (data) config.data = data
      const response = await api(config)
      return response.data
    } catch (e) {
      const msg = e.response?.data?.msg || e.message || 'Something went wrong'
      if (!options.silent) toast.error(msg)
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    loading,
    get: (url, params) => call('get', url, null, { params }),
    post: (url, data, opts) => call('post', url, data, opts),
    put: (url, data, opts) => call('put', url, data, opts),
    del: (url, opts) => call('delete', url, null, opts),
  }
}
