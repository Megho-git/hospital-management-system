import { reactive } from 'vue'

export const store = reactive({
  user: JSON.parse(localStorage.getItem('user') || 'null'),
  token: localStorage.getItem('token') || '',
  refreshToken: localStorage.getItem('refresh_token') || '',
  notifications: [],
  unreadCount: 0,
  sidebarOpen: false,

  toasts: [],
  _toastId: 0,

  login(token, refreshToken, user) {
    this.token = token
    this.refreshToken = refreshToken || ''
    this.user = user
    localStorage.setItem('token', token)
    if (refreshToken) localStorage.setItem('refresh_token', refreshToken)
    localStorage.setItem('user', JSON.stringify(user))
  },

  logout() {
    this.token = ''
    this.refreshToken = ''
    this.user = null
    this.notifications = []
    this.unreadCount = 0
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  },

  get isLoggedIn() {
    return !!this.token
  },

  get role() {
    return this.user?.role || ''
  },

  addToast(type, message, duration = 4000) {
    const id = ++this._toastId
    this.toasts.push({ id, type, message })
    if (duration > 0) {
      setTimeout(() => this.removeToast(id), duration)
    }
  },

  removeToast(id) {
    const idx = this.toasts.findIndex(t => t.id === id)
    if (idx !== -1) this.toasts.splice(idx, 1)
  },

  toggleSidebar() {
    this.sidebarOpen = !this.sidebarOpen
  },
})
