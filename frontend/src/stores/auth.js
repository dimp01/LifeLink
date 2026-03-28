import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '../services/api.js'

export const useAuthStore = defineStore('auth', () => {
  const user = ref(JSON.parse(sessionStorage.getItem('user') || 'null'))
  const accessToken = ref(sessionStorage.getItem('access_token') || '')
  const csrfToken = ref('')
  const isTokenRefreshing = ref(false)
  const refreshTokenPromise = ref(null)

  // Personalization features
  const userPreferences = ref(JSON.parse(localStorage.getItem('userPreferences') || 'null') || {
    theme: 'light',
    language: 'en',
    notifications: {
      email: true,
      push: true,
      sms: false,
      donationReminders: true,
      communityUpdates: true,
      medicalAlerts: true,
    },
    privacy: {
      profileVisibility: 'public',
      showDonationHistory: true,
      allowMessages: true,
    },
    dashboard: {
      widgets: ['stats', 'recent-activity', 'upcoming-events', 'quick-actions'],
      layout: 'grid',
      compactView: false,
    }
  })

  const isLoggedIn = computed(() => !!user.value)
  const role = computed(() => user.value?.role || '')

  const dashboardRoute = computed(() => {
    if (role.value === 'admin') return '/admin'
    if (role.value === 'hospital') return '/hospital'
    if (role.value === 'recipient') return '/recipient'
    return '/donor'
  })

  /**
   * Update user preferences
   */
  function updatePreferences(newPreferences) {
    userPreferences.value = { ...userPreferences.value, ...newPreferences }
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences.value))
  }

  /**
   * Update notification settings
   */
  function updateNotifications(notificationSettings) {
    userPreferences.value.notifications = { ...userPreferences.value.notifications, ...notificationSettings }
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences.value))
  }

  /**
   * Update dashboard settings
   */
  function updateDashboardSettings(dashboardSettings) {
    userPreferences.value.dashboard = { ...userPreferences.value.dashboard, ...dashboardSettings }
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences.value))
  }

  /**
   * Toggle theme
   */
  function toggleTheme() {
    userPreferences.value.theme = userPreferences.value.theme === 'light' ? 'dark' : 'light'
    localStorage.setItem('userPreferences', JSON.stringify(userPreferences.value))
    applyTheme()
  }

  /**
   * Apply theme to document
   */
  function applyTheme() {
    const theme = userPreferences.value.theme
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }
  async function getCsrfToken() {
    try {
      const res = await api.get('/auth/csrf-token')
      csrfToken.value = res.data.csrf_token
      return csrfToken.value
    } catch (error) {
      console.error('Failed to get CSRF token:', error)
      throw error
    }
  }


  /**
   * Login with email and password
   * Server sets HttpOnly cookie with session
   * No tokens stored in client-side storage (more secure)
   */
  async function login(email, password) {
    try {
      // Get CSRF token first
      await getCsrfToken()

      // Use URLSearchParams for form-urlencoded data (OAuth2PasswordRequestForm requirement)
      const params = new URLSearchParams()
      params.append('username', email)
      params.append('password', password)

      const res = await api.post('/auth/login', params.toString(), {
        headers: {
          'X-CSRF-Token': csrfToken.value,
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      })

      // Store user info in sessionStorage (not localStorage for security)
      // Access token is in memory, refresh token is in HttpOnly cookie
      accessToken.value = res.data.access_token
      sessionStorage.setItem('access_token', accessToken.value)

      user.value = {
        role: res.data.role,
        full_name: res.data.full_name,
        user_id: res.data.user_id,
        email: email,
      }
      sessionStorage.setItem('user', JSON.stringify(user.value))

      // Load user preferences and apply theme
      applyTheme()

      return res.data
    } catch (error) {
      console.error('Login failed:', error)
      throw error
    }
  }

  /**
   * Register new user
   */
  async function register(payload) {
    try {
      // Get CSRF token first
      await getCsrfToken()

      const res = await api.post('/auth/register', payload, {
        headers: {
          'X-CSRF-Token': csrfToken.value,
        },
      })
      return res.data
    } catch (error) {
      console.error('Registration failed:', error)
      throw error
    }
  }

  /**
   * Refresh access token using refresh token in cookie
   * Called automatically by API interceptor on 401
   */
  async function refreshAccessToken() {
    // Prevent multiple simultaneous refresh attempts
    if (isTokenRefreshing.value) {
      return refreshTokenPromise.value
    }

    isTokenRefreshing.value = true

    refreshTokenPromise.value = (async () => {
      try {
        // Get CSRF token for this request
        await getCsrfToken()

        const res = await api.post(
          '/auth/refresh',
          {},
          {
            headers: {
              'X-CSRF-Token': csrfToken.value,
            },
          }
        )

        accessToken.value = res.data.access_token
        sessionStorage.setItem('access_token', accessToken.value)

        isTokenRefreshing.value = false
        return res.data
      } catch (error) {
        console.error('Token refresh failed:', error)
        isTokenRefreshing.value = false
        // If refresh fails, logout user
        await logout()
        throw error
      }
    })()

    return refreshTokenPromise.value
  }

  /**
   * Logout - clear user and revoke session
   */
  async function logout() {
    try {
      // Get CSRF token
      await getCsrfToken()

      // Call logout endpoint to revoke session
      await api.post(
        '/auth/logout',
        {},
        {
          headers: {
            'X-CSRF-Token': csrfToken.value,
          },
        }
      )
    } catch (error) {
      console.error('Logout error:', error)
      // Clear local state even if server request fails
    } finally {
      window.location.href = `/login#${user.value.role}`
      user.value = null
      accessToken.value = ''
      csrfToken.value = ''
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('access_token')
      // Note: Keep user preferences in localStorage for next login
    }
  }

  /**
   * Restore authentication state on page load
   * Verify session with server by calling /auth/me
   */
  async function restoreSession() {
    try {
      // Check if user data exists in sessionStorage
      const savedUser = sessionStorage.getItem('user')
      if (!savedUser) {
        return false
      }

      // Verify session with server
      const res = await api.get('/auth/me')

      user.value = {
        ...JSON.parse(savedUser),
        email: res.data.email,
        full_name: res.data.full_name,
      }

      // Get initial CSRF token
      await getCsrfToken()

      // Apply theme
      applyTheme()

      return true
    } catch (error) {
      // Session invalid or expired
      user.value = null
      sessionStorage.removeItem('user')
      return false
    }
  }

  // Initialize theme on store creation
  applyTheme()

  return {
    user,
    accessToken,
    csrfToken,
    userPreferences,
    isLoggedIn,
    role,
    dashboardRoute,
    getCsrfToken,
    login,
    register,
    refreshAccessToken,
    logout,
    restoreSession,
    updatePreferences,
    updateNotifications,
    updateDashboardSettings,
    toggleTheme,
    applyTheme,
  }
})

