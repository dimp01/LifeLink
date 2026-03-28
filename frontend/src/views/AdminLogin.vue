<template>
  <div class="auth-page">
    <!-- Left Panel -->
    <div class="auth-panel">
      <router-link to="/" class="auth-logo">
        <div class="logo-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white">
            <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
          </svg>
        </div>
        <span>LifeLink AI</span>
      </router-link>

      <div class="auth-panel-content">
        <h2>Admin Portal<br/>Access</h2>
        <p>
          Secure administrative access for system management,
          user oversight, and platform analytics.
        </p>

        <div class="panel-stats">
          <div v-for="s in panelStats" :key="s.label" class="panel-stat">
            <div class="ps-value">{{ s.value }}</div>
            <div class="ps-label">{{ s.label }}</div>
          </div>
        </div>
      </div>

      <div class="panel-quote">
        "Managing the future of organ donation."
      </div>
    </div>

    <!-- Right Panel -->
    <div class="auth-form-side">
      <div class="auth-card">
        <div class="auth-card-header">
          <h2>Admin Portal Login</h2>
          <p>Access your admin dashboard</p>
        </div>

        <div v-if="error" class="alert alert-error">{{ error }}</div>

        <form @submit.prevent="handleLogin">
          <div class="form-group">
            <label>Admin Email</label>
            <input
              v-model="email"
              type="email"
              placeholder="admin@lifelink.ai"
              required
              autocomplete="email"
            />
          </div>

          <div class="form-group">
            <label>Password</label>
            <input
              v-model="password"
              type="password"
              placeholder="Your password"
              required
              autocomplete="current-password"
            />
          </div>

          <button class="btn btn-primary w-full" type="submit" :disabled="loading">
            <span v-if="loading" class="btn-spinner"></span>
            {{ loading ? 'Accessing…' : 'Access Portal' }}
          </button>
        </form>

        <div class="auth-footer-links">
          <div class="auth-footer-link">
            ← <router-link to="/login">Back to Patient Login</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const email = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

const panelStats = [
  { value: '50K+', label: 'Users' },
  { value: '500+', label: 'Hospitals' },
  { value: '24/7', label: 'Monitoring' },
]

function updateDocumentTitle() {
  document.title = `Admin Login – LifeLink AI`
}

async function handleLogin() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    router.push(auth.dashboardRoute)
  } catch (e) {
    error.value =
      e.response?.data?.detail || 'Invalid credentials. Please try again.'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  updateDocumentTitle()
  if (auth.isLoggedIn && auth.role !== 'admin') {
    error.value = `You are currently logged in as ${auth.role}. Please log out before switching to admin.`
  }
})
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
}

/* Left panel */
.auth-panel {
  background: var(--primary);
  border-right: 3px solid #000;
  padding: 40px;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}
.auth-panel::before { display: none; }
.auth-panel::after  { display: none; }
.auth-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #fff;
  font-size: 18px;
  font-weight: 800;
}
.logo-icon {
  width: 34px; height: 34px;
  border-radius: 4px;
  background: rgba(255,255,255,0.2);
  border: 2px solid rgba(255,255,255,0.5);
  display: flex; align-items: center; justify-content: center;
}
.auth-panel-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
}
.auth-panel-content h2 {
  font-size: 46px;
  font-weight: 900;
  color: #fff;
  line-height: 1.05;
  letter-spacing: -0.03em;
  margin-bottom: 20px;
}
.auth-panel-content p {
  font-size: 15px;
  color: rgba(255,255,255,0.85);
  line-height: 1.7;
  margin-bottom: 40px;
  max-width: 340px;
  font-weight: 500;
}
.panel-stats { display: flex; gap: 28px; }
.ps-value { font-size: 28px; font-weight: 900; color: var(--accent); letter-spacing: -0.02em; }
.ps-label { font-size: 11px; color: rgba(255,255,255,0.65); margin-top: 2px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.panel-quote {
  background: rgba(255,255,255,0.12);
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 4px;
  padding: 12px 16px;
  color: rgba(255,255,255,0.8);
  font-size: 13px;
  font-style: italic;
  position: relative;
  z-index: 1;
}

/* Right side */
.auth-form-side {
  background: var(--bg);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 40px;
}
.auth-card {
  width: 100%;
  max-width: 400px;
}
.auth-card-header { margin-bottom: 32px; }
.auth-card-header h2 {
  font-size: 26px;
  font-weight: 900;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.auth-card-header p { color: var(--text-muted); font-size: 14px; font-weight: 500; }

/* Auth divider */
.auth-divider {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 24px 0;
  color: var(--text-faint);
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.auth-divider::before, .auth-divider::after {
  content: '';
  flex: 1;
  height: 2px;
  background: #000;
}

/* Demo accounts */
.demo-accounts { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 28px; }
.demo-btn {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 12px 14px;
  background: #fff;
  border: 2px solid #000;
  border-radius: 4px;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
  font-family: var(--font);
  text-align: left;
  box-shadow: 3px 3px 0 #000;
}
.demo-btn:hover { transform: translate(-1px,-1px); box-shadow: 4px 4px 0 #000; background: var(--accent); }
.demo-btn:active { transform: translate(1px,1px); box-shadow: 2px 2px 0 #000; }
.demo-btn.active {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
  box-shadow: 3px 3px 0 var(--primary);
}
.demo-btn.active .demo-role { color: white; }
.demo-btn.active .demo-fill { color: rgba(255,255,255,0.8); }
.demo-role { font-size: 13px; font-weight: 800; color: var(--text); }
.demo-fill { font-size: 11px; color: var(--text-muted); font-weight: 500; }

/* Footer Links */
.auth-footer-links { margin-top: 24px; }
.auth-footer-link {
  text-align: center;
  font-size: 14px;
  color: var(--text-muted);
  font-weight: 500;
  margin-bottom: 8px;
}
.auth-footer-link:last-child { margin-bottom: 0; }
.auth-footer-link a { color: var(--primary); font-weight: 800; text-decoration: none; }
.auth-footer-link a:hover { text-decoration: underline; }

@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-panel { padding: 32px 24px; min-height: 200px; border-right: none; border-bottom: 3px solid #000; }
  .auth-panel-content h2 { font-size: 30px; }
  .auth-panel-content { justify-content: flex-start; }
  .auth-form-side { padding: 36px 24px; }
  .auth-card { max-width: 100%; }
}
</style>