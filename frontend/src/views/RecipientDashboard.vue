<template>
  <div class="dashboard">
    <header class="dashboard-header">
      <h1>Recipient Dashboard</h1>
      <p>Welcome, {{ user.full_name }}. Track your verification and transplant readiness.</p>
    </header>

    <section class="status-card">
      <div class="status-row">
        <div class="status-item">
          <div class="status-label">Verification</div>
          <div class="status-value">{{ verification.status }}</div>
        </div>
        <div class="status-item">
          <div class="status-label">Submitted</div>
          <div class="status-value">{{ verification.submittedAt ? formatDate(verification.submittedAt) : '—' }}</div>
        </div>
        <div class="status-item">
          <div class="status-label">ETA</div>
          <div class="status-value">{{ verification.eta || 'TBD' }}</div>
        </div>
      </div>
    </section>

    <section class="action-section">
      <div v-if="verification.status === 'Not started'" class="action-card">
        <h2>Start your Legal Verification</h2>
        <p>
          Complete the verification form so hospitals can review your case and match you to a transplant.
          You can save your progress and return later.
        </p>
        <button class="btn btn-primary" @click="goToVerification">Begin verification</button>
      </div>

      <div v-else class="action-card">
        <h2>Verification in progress</h2>
        <p>
          Your documents are being reviewed. You can reopen the verification form to update details or view the summary.
        </p>
        <div class="action-buttons">
          <button class="btn btn-secondary" @click="goToVerification">Continue verification</button>
          <button class="btn btn-outline" @click="goToSummary">View summary</button>
        </div>
      </div>
    </section>

    <section class="profile-card">
      <h3>Your profile</h3>
      <div class="profile-grid">
        <div><strong>Name</strong><span>{{ user.full_name }}</span></div>
        <div><strong>Email</strong><span>{{ user.email }}</span></div>
        <div><strong>Role</strong><span>{{ user.role }}</span></div>
        <div><strong>User ID</strong><span>{{ user.user_id }}</span></div>
      </div>
    </section>

    <section class="info-card">
      <h3>Next steps</h3>
      <ul>
        <li>Complete your verification form</li>
        <li>Wait for review (typically 5-7 business days)</li>
        <li>Receive notification when verified</li>
      </ul>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const user = computed(() => auth.user || {})

const storageKey = `recipientVerification_${user.value?.user_id}`

const defaultState = {
  status: 'Not started',
  step: 1,
  submittedAt: null,
  eta: null,
  data: {},
}

function readState() {
  try {
    const raw = localStorage.getItem(storageKey)
    return raw ? JSON.parse(raw) : { ...defaultState }
  } catch {
    return { ...defaultState }
  }
}

function writeState(state) {
  localStorage.setItem(storageKey, JSON.stringify(state))
}

const verification = readState()

function goToVerification() {
  router.push('/recipient/verify')
}

function goToSummary() {
  router.push({ name: 'RecipientVerification', query: { view: 'summary' } })
}

// Removed auto-redirect - let user click the button to start verification
// onMounted(() => {
//   if (verification.status === 'Not started') {
//     goToVerification()
//   }
// })

function formatDate(value) {
  if (!value) return '—'
  return new Date(value).toLocaleDateString()
}
</script>

<style scoped>
.dashboard {
  max-width: 980px;
  margin: 0 auto;
  padding: 40px 16px;
}
.dashboard-header {
  margin-bottom: 32px;
}
.dashboard-header h1 {
  font-size: 32px;
  margin-bottom: 12px;
}
.dashboard-header p {
  color: var(--text-muted);
  font-size: 15px;
  margin: 0;
}

.status-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 28px;
  box-shadow: var(--shadow);
}
.status-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 18px;
}
.status-item {
  padding: 14px;
  background: var(--bg-subtle);
  border: 2px solid rgba(0,0,0,0.08);
  border-radius: 6px;
  text-align: center;
}
.status-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 10px;
}
.status-value {
  font-size: 18px;
  font-weight: 900;
}

.action-section {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
  margin-bottom: 28px;
}
.action-card {
  flex: 1;
  min-width: 260px;
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--shadow);
}
.action-card h2 {
  margin-top: 0;
  margin-bottom: 14px;
}
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 16px;
}

.profile-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 28px;
}
.profile-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  margin-top: 14px;
}
.profile-grid div {
  display: flex;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--bg-subtle);
  border: 1px solid rgba(0,0,0,0.08);
  border-radius: 6px;
}
.profile-grid strong { font-weight: 700; color: var(--text-muted); }

.info-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--shadow);
}
.info-card h3 { margin-top: 0; }
.info-card ul { padding-left: 20px; margin: 0; }
.info-card li { margin-bottom: 8px; }

@media (max-width: 768px) {
  .status-row { grid-template-columns: 1fr; }
  .profile-grid { grid-template-columns: 1fr; }
  .action-section { flex-direction: column; }
}
</style>
