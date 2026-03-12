import axios from 'axios'

const api = axios.create({ baseURL: '/api' })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = false
let refreshWaiters = []

function waitForRefresh() {
  return new Promise((resolve, reject) => refreshWaiters.push({ resolve, reject }))
}

function resolveRefresh(token) {
  refreshWaiters.forEach(w => w.resolve(token))
  refreshWaiters = []
}

function rejectRefresh(err) {
  refreshWaiters.forEach(w => w.reject(err))
  refreshWaiters = []
}

api.interceptors.response.use(
  res => res,
  async err => {
    const original = err.config
    const isAuthRoute = original?.url?.includes('/auth/login') || original?.url?.includes('/auth/register') || original?.url?.includes('/auth/refresh')

    if (err.response?.status !== 401 || isAuthRoute || original?._retry) {
      return Promise.reject(err)
    }

    original._retry = true
    const refreshToken = localStorage.getItem('refresh_token')
    if (!refreshToken) {
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(err)
    }

    try {
      if (refreshing) {
        const newToken = await waitForRefresh()
        original.headers.Authorization = `Bearer ${newToken}`
        return api(original)
      }

      refreshing = true
      const res = await axios.post('/api/auth/refresh', null, { headers: { Authorization: `Bearer ${refreshToken}` } })
      const newToken = res.data?.token
      if (!newToken) throw new Error('No token in refresh response')
      localStorage.setItem('token', newToken)
      if (res.data?.user) localStorage.setItem('user', JSON.stringify(res.data.user))
      resolveRefresh(newToken)
      original.headers.Authorization = `Bearer ${newToken}`
      return api(original)
    } catch (e) {
      rejectRefresh(e)
      localStorage.clear()
      window.location.href = '/login'
      return Promise.reject(err)
    } finally {
      refreshing = false
    }
  }
)

export default api
