import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router/index.js'
import './assets/style.css'

const app = createApp(App)
const pinia = createPinia()

app.use(pinia)
app.use(router)

// Restore authentication session before mounting app
// This ensures the user is properly authenticated if returning to the app
const { useAuthStore } = await import('./stores/auth.js')
const authStore = useAuthStore()

console.log(authStore.csrfToken) // Debug: Check if user is loaded from session

// Restore session from server
await authStore.restoreSession()

app.mount('#app')
