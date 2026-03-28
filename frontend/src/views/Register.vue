<template>
  <div class="auth-page">
    <!-- Left Panel -->
    <div class="auth-panel">
      <router-link to="/" class="auth-logo">
        <div class="logo-icon">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        </div>
        <span>LifeLink AI</span>
      </router-link>

      <div class="auth-panel-content">
        <h2>Join the movement.<br/>Save lives.</h2>
        <p>Register today and become part of India's largest organ donor network powered by AI.</p>
        <ul class="benefits-list">
          <li v-for="b in benefits" :key="b"><span class="check">✓</span>{{ b }}</li>
        </ul>
      </div>

      <div class="panel-quote">"One decision. Eight lives changed forever."</div>
    </div>

    <!-- Right Panel -->
    <div class="auth-form-side">
      <div class="auth-card">
        <div class="auth-card-header">
          <h2>Create account</h2>
          <p>Join LifeLink AI as a donor, recipient, or hospital</p>
        </div>

        <div v-if="error"   class="alert alert-error">{{ error }}</div>
        <div v-if="success" class="alert alert-success">{{ success }}</div>

        <form @submit.prevent="handleRegister">
          <div class="form-group">
            <label>Full name</label>
            <input v-model="form.full_name" type="text" placeholder="Your full name" required />
          </div>
          <div class="form-group">
            <label>Email address</label>
            <input v-model="form.email" type="email" placeholder="you@example.com" required autocomplete="email" />
          </div>
          <div class="form-group">
            <label>Password</label>
            <input v-model="form.password" type="password" placeholder="Min 6 characters" required minlength="6" autocomplete="new-password" />
          </div>
          <div class="form-group">
            <label>Account type</label>
            <select v-model="form.role">
              <option value="donor">Donor — I want to register as an organ donor</option>
              <option value="recipient">Recipient — I need an organ transplant</option>
              <option value="hospital">Hospital — I manage a hospital / transplant centre</option>
            </select>
          </div>
          <button class="btn btn-primary w-full" type="submit" :disabled="loading">
            <span v-if="loading" class="btn-spinner"></span>
            {{ loading ? 'Creating account…' : 'Create account' }}
          </button>
        </form>

        <div class="auth-footer-link">
          Already have an account? <router-link to="/login">Sign in →</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()
const loading = ref(false)
const error   = ref('')
const success = ref('')

const form = reactive({ full_name: '', email: '', password: '', role: 'donor' })

const benefits = [
  'Free registration — no hidden fees',
  'Your wishes are legally protected',
  'AI matches you to the right hospital',
  'Update or withdraw consent anytime',
]

async function handleRegister() {
  loading.value = true; error.value = ''; success.value = ''
  try {
    await auth.register(form)
    success.value = 'Account created! Redirecting…'
    setTimeout(() => {
      if (form.role === 'hospital') {
        router.push('/login-hospital')
      } else {
        router.push(`/login#${form.role}`)
      }
    }, 1200)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Registration failed. Please try again.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1fr 1fr;
}
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
  display: flex; align-items: center; gap: 10px;
  text-decoration: none; color: #fff;
  font-size: 18px; font-weight: 800;
}
.logo-icon {
  width: 34px; height: 34px;
  border-radius: 4px;
  background: rgba(255,255,255,0.2);
  border: 2px solid rgba(255,255,255,0.5);
  display: flex; align-items: center; justify-content: center;
}
.auth-panel-content {
  flex: 1; display: flex; flex-direction: column;
  justify-content: center; position: relative; z-index: 1;
}
.auth-panel-content h2 {
  font-size: 42px; font-weight: 900; color: #fff;
  line-height: 1.05; letter-spacing: -0.03em; margin-bottom: 18px;
}
.auth-panel-content p {
  font-size: 15px; color: rgba(255,255,255,0.85);
  line-height: 1.7; margin-bottom: 32px; max-width: 340px; font-weight: 500;
}
.benefits-list { list-style: none; display: flex; flex-direction: column; gap: 12px; }
.benefits-list li {
  display: flex; align-items: center; gap: 10px;
  color: rgba(255,255,255,0.95); font-size: 14px; font-weight: 600;
}
.check {
  width: 20px; height: 20px;
  background: var(--accent);
  border: 2px solid rgba(255,255,255,0.7);
  border-radius: 3px;
  display: flex; align-items: center; justify-content: center;
  font-size: 11px; font-weight: 900; flex-shrink: 0; color: #000;
}
.panel-quote {
  background: rgba(255,255,255,0.12);
  border: 2px solid rgba(255,255,255,0.3);
  border-radius: 4px;
  padding: 12px 16px;
  color: rgba(255,255,255,0.8); font-size: 13px;
  font-style: italic; position: relative; z-index: 1;
}
.auth-form-side {
  background: var(--bg);
  display: flex; align-items: center; justify-content: center;
  padding: 48px 40px;
}
.auth-card { width: 100%; max-width: 420px; }
.auth-card-header { margin-bottom: 28px; }
.auth-card-header h2 { font-size: 26px; font-weight: 900; letter-spacing: -0.02em; margin-bottom: 6px; }
.auth-card-header p { color: var(--text-muted); font-size: 14px; font-weight: 500; }
.btn-spinner {
  width: 14px; height: 14px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.auth-footer-link {
  text-align: center; font-size: 14px; color: var(--text-muted); margin-top: 24px; font-weight: 500;
}
.auth-footer-link a { color: var(--primary); font-weight: 800; text-decoration: none; }
.auth-footer-link a:hover { text-decoration: underline; }
@media (max-width: 768px) {
  .auth-page { grid-template-columns: 1fr; }
  .auth-panel { padding: 32px 24px; min-height: 200px; border-right: none; border-bottom: 3px solid #000; }
  .auth-panel-content h2 { font-size: 28px; }
  .auth-panel-content { justify-content: flex-start; padding-top: 24px; }
  .auth-form-side { padding: 32px 20px; }
}
</style>
