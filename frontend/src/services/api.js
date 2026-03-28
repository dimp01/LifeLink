import axios from 'axios'

const api = axios.create({
  baseURL: 'https://ominous-rotary-phone-rj5xp5q76rwfwx6j-8000.app.github.dev/',
  timeout: 30000,
  withCredentials: true, // Include cookies in requests
})

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  isRefreshing = false
  failedQueue = []
}

/**
 * Request Interceptor
 * Adds CSRF token to all requests
 */
api.interceptors.request.use((config) => {
  // Attach access token if available
  const accessToken = sessionStorage.getItem('access_token')
  if (accessToken) {
    config.headers['Authorization'] = `Bearer ${accessToken}`
  }

  // Get CSRF token from sessionStorage
  const csrfToken = sessionStorage.getItem('csrf_token')
  if (csrfToken) {
    config.headers['X-CSRF-Token'] = csrfToken
  }

  return config
})

/**
 * Response Interceptor
 * Handles 401 by refreshing token and retrying request
 * Handles other errors appropriately
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const { config, response } = error

    if (response?.status === 401 && !config?.retry) {
      if (isRefreshing) {
        // Queue request if already refreshing
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(() => api(config))
          .catch((err) => Promise.reject(err))
      }

      isRefreshing = true
      config.retry = true

      try {
        // Import auth store here to avoid circular dependency
        const { useAuthStore } = await import('../stores/auth.js')
        const authStore = useAuthStore()

        // Attempt to refresh token
        await authStore.refreshAccessToken()

        // Get new CSRF token
        const csrfToken = await authStore.getCsrfToken()
        sessionStorage.setItem('csrf_token', csrfToken)
        config.headers['X-CSRF-Token'] = csrfToken

        processQueue(null, csrfToken)

        // Retry the original request
        return api(config)
      } catch (err) {
        processQueue(err, null)

        // If refresh fails, redirect to login
        window.location.href = '/login'
        return Promise.reject(err)
      }
    }

    // For 403 (CSRF token invalid), try to get new one
    if (response?.status === 403 && response?.data?.detail?.includes('CSRF')) {
      try {
        const { useAuthStore } = await import('../stores/auth.js')
        const authStore = useAuthStore()
        const csrfToken = await authStore.getCsrfToken()
        sessionStorage.setItem('csrf_token', csrfToken)
        config.headers['X-CSRF-Token'] = csrfToken
        return api(config)
      } catch (err) {
        return Promise.reject(err)
      }
    }

    return Promise.reject(error)
  }
)

export default api
