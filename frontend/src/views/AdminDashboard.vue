<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title">Admin Dashboard</h1>
      <p class="page-subtitle">Manage donors, content and ML training</p>

      <!-- Tabs -->
      <div class="tabs">
        <button v-for="tab in tabs" :key="tab.id"
          class="tab-btn" :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id">
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Analytics Tab -->
      <div v-if="activeTab === 'analytics'">
        <div v-if="analyticsLoading" class="spinner"></div>
        <template v-else-if="analytics">
          <div class="grid-4" style="margin-bottom:28px">
            <div class="stat-card"><div class="stat-icon">🩸</div><div class="stat-value">{{ analytics.total_donors }}</div><div class="stat-label">Total Donors</div></div>
            <div class="stat-card"><div class="stat-icon">⏳</div><div class="stat-value">{{ analytics.pending_donors }}</div><div class="stat-label">Pending</div></div>
            <div class="stat-card" style="border-color:var(--success)">
              <div class="stat-icon" style="background:var(--success-light,#dcfce7)">✅</div>
              <div class="stat-value" style="color:var(--success)">{{ analytics.approved_donors }}</div>
              <div class="stat-label">Approved</div>
            </div>
            <div class="stat-card" style="border-color:var(--accent)">
              <div class="stat-icon" style="background:#fef9c3">👥</div>
              <div class="stat-value" style="color:var(--accent)">{{ analytics.total_users }}</div>
              <div class="stat-label">Total Users</div>
            </div>
          </div>
          <div class="grid-2">
            <div class="card">
              <div class="card-header">Blood Group Distribution</div>
              <Doughnut v-if="bloodChart" :data="bloodChart" :options="{ responsive: true }" />
            </div>
            <div class="card">
              <div class="card-header">Top Regions</div>
              <Bar v-if="regionChart" :data="regionChart" :options="{ responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }" />
            </div>
          </div>
        </template>
      </div>

      <!-- Donors Tab -->
      <div v-if="activeTab === 'donors'">
        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between">
            <span>All Donors</span>
            <select v-model="statusFilter" class="filter-select">
              <option value="">All Status</option>
              <option value="pending">Pending</option>
              <option value="approved">Approved</option>
              <option value="rejected">Rejected</option>
            </select>
          </div>
          <div v-if="donorsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Age</th>
                  <th>Blood</th>
                  <th>Location</th>
                  <th>Organs</th>
                  <th>Status</th>
                  <th>Registered</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in donors" :key="d.id">
                  <td>{{ d.full_name }}</td>
                  <td>{{ d.age }}</td>
                  <td>{{ d.blood_group }}</td>
                  <td>{{ d.location }}</td>
                  <td>
                    <span class="badge badge-info" v-for="o in (d.organs_selected || []).slice(0,2)" :key="o">{{ o }}</span>
                    <span v-if="d.organs_selected?.length > 2" class="badge badge-info">+{{ d.organs_selected.length - 2 }}</span>
                  </td>
                  <td><span class="badge" :class="statusClass(d.status)">{{ d.status }}</span></td>
                  <td>{{ new Date(d.created_at).toLocaleDateString() }}</td>
                  <td>
                    <div class="action-btns">
                      <button v-if="d.status !== 'approved'" class="btn btn-sm btn-accent" @click="updateStatus(d.id, 'approved')">✓ Approve</button>
                      <button v-if="d.status !== 'rejected'" class="btn btn-sm btn-outline" @click="updateStatus(d.id, 'rejected')">✗ Reject</button>
                    </div>
                  </td>
                </tr>
                <tr v-if="donors.length === 0">
                  <td colspan="8" style="text-align:center;color:var(--text-muted)">No donors found</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- ML Training Tab -->
      <div v-if="activeTab === 'ml'">
        <div class="card">
          <div class="card-header">ML Training Control</div>
          <div class="ml-status-box">
            <div class="ml-status-icon">{{ trainingStatus === 'completed' ? '✅' : trainingStatus === 'running' ? '⚙️' : trainingStatus === 'failed' ? '❌' : '🤖' }}</div>
            <div>
              <div class="ml-status-text">Status: <strong>{{ trainingStatus?.toUpperCase() || 'IDLE' }}</strong></div>
              <div v-if="lastTrained" class="ml-last">Last trained: {{ lastTrained }}</div>
            </div>
          </div>
          <div v-if="trainMsg" class="alert alert-success">{{ trainMsg }}</div>
          <button class="btn btn-primary btn-lg" @click="triggerTraining" :disabled="trainingStatus === 'running'">
            {{ trainingStatus === 'running' ? '⚙️ Training in progress...' : '🚀 Start ML Training' }}
          </button>
          <p class="ml-note">Training will process the Organ Donation CSV dataset and generate forecasts, ODII, and SHAP explanations. This may take 30–60 seconds.</p>
        </div>
      </div>

      <!-- System Logs Tab -->
      <div v-if="activeTab === 'system'">
        <div class="grid-2">
          <div class="card">
            <div class="card-header">🤖 LifeLink AI Chat Logs</div>
            <div v-if="logsLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>User</th>
                    <th>Query</th>
                    <th>Topic</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="log in chatLogs" :key="log.id">
                    <td>User #{{ log.user_id }}</td>
                    <td class="truncate" :title="log.query">{{ log.query }}</td>
                    <td><span class="badge" :class="log.is_organ_related ? 'badge-success' : 'badge-warning'">{{ log.is_organ_related ? 'Organ' : 'Other' }}</span></td>
                    <td style="font-size:10px">{{ new Date(log.created_at).toLocaleString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <div class="card">
            <div class="card-header">📜 Model Version History</div>
            <div v-if="logsLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Version</th>
                    <th>Accuracy</th>
                    <th>Trained At</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="v in modelVersions" :key="v.id">
                    <td style="font-weight:900">v{{ v.version_tag }}</td>
                    <td>{{ (v.accuracy * 100).toFixed(1) }}%</td>
                    <td>{{ new Date(v.created_at).toLocaleDateString() }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>

      <!-- Content Tab -->
      <div v-if="activeTab === 'content'">
        <div class="card">
          <div class="card-header">Add Awareness Content</div>
          <div v-if="contentMsg" class="alert alert-success">{{ contentMsg }}</div>
          <form @submit.prevent="submitContent">
            <div class="form-group">
              <label>Title</label>
              <input v-model="contentForm.title" type="text" required />
            </div>
            <div class="form-group">
              <label>Type</label>
              <select v-model="contentForm.type" required>
                <option value="myth">Myth vs Fact</option>
                <option value="faq">FAQ</option>
                <option value="blog">Blog / Article</option>
                <option value="legal">Legal Info</option>
              </select>
            </div>
            <div class="form-group">
              <label>Content</label>
              <textarea v-model="contentForm.content" rows="5" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="contentLoading">
              {{ contentLoading ? 'Publishing...' : 'Publish Content' }}
            </button>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, ArcElement,
  Title, Tooltip, Legend
} from 'chart.js'
import api from '../services/api.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, ArcElement, Title, Tooltip, Legend)

const activeTab = ref('analytics')
const tabs = [
  { id: 'analytics', label: 'Analytics', icon: '📊' },
  { id: 'donors', label: 'Donors', icon: '👥' },
  { id: 'ml', label: 'ML Training', icon: '🤖' },
  { id: 'system', label: 'System Logs', icon: '📋' },
  { id: 'content', label: 'Content', icon: '📝' },
]

// Analytics
const analytics = ref(null)
const analyticsLoading = ref(false)
const bloodChart = computed(() => {
  if (!analytics.value?.blood_group_distribution) return null
  const data = analytics.value.blood_group_distribution
  return {
    labels: Object.keys(data),
    datasets: [{ data: Object.values(data), backgroundColor: ['#e53e3e','#38b2ac','#ed8936','#9f7aea','#4299e1','#48bb78','#f687b3','#ecc94b'] }],
  }
})
const regionChart = computed(() => {
  if (!analytics.value?.top_regions) return null
  return {
    labels: analytics.value.top_regions.map(r => r.region),
    datasets: [{ label: 'Donors', data: analytics.value.top_regions.map(r => r.count), backgroundColor: '#e53e3e' }],
  }
})

// Donors
const donors = ref([])
const donorsLoading = ref(false)
const statusFilter = ref('')

// ML
const trainingStatus = ref('idle')
const lastTrained = ref(null)
const trainMsg = ref('')

// Content
const contentForm = ref({ title: '', type: 'myth', content: '' })
const contentMsg = ref('')
const contentLoading = ref(false)

// System Logs
const chatLogs = ref([])
const modelVersions = ref([])
const logsLoading = ref(false)

function statusClass(s) {
  return { pending: 'badge-warning', approved: 'badge-success', rejected: 'badge-danger' }[s] || 'badge-info'
}

async function loadAnalytics() {
  analyticsLoading.value = true
  try {
    const res = await api.get('/admin/analytics')
    analytics.value = res.data
  } finally {
    analyticsLoading.value = false
  }
}

async function loadDonors() {
  donorsLoading.value = true
  try {
    const params = statusFilter.value ? { status: statusFilter.value } : {}
    const res = await api.get('/admin/donors', { params })
    donors.value = res.data
  } finally {
    donorsLoading.value = false
  }
}

async function updateStatus(id, status) {
  await api.put(`/admin/donors/${id}/status`, { status })
  await loadDonors()
}

async function triggerTraining() {
  trainMsg.value = ''
  const res = await api.post('/ml/train')
  trainingStatus.value = 'running'
  trainMsg.value = res.data.message
  // Poll status
  const poll = setInterval(async () => {
    try {
      const r = await api.get('/ml/training-status')
      trainingStatus.value = r.data.status
      if (r.data.last_trained) lastTrained.value = r.data.last_trained
      if (r.data.status !== 'running') clearInterval(poll)
    } catch { clearInterval(poll) }
  }, 3000)
}

async function submitContent() {
  contentLoading.value = true
  contentMsg.value = ''
  try {
    await api.post('/admin/awareness', contentForm.value)
    contentMsg.value = 'Content published successfully!'
    contentForm.value = { title: '', type: 'myth', content: '' }
  } finally {
    contentLoading.value = false
  }
}

async function loadSystemLogs() {
  logsLoading.value = true
  try {
    const [chatRes, modelRes] = await Promise.all([
      api.get('/admin/chat-logs'),
      api.get('/admin/model-versions')
    ])
    chatLogs.value = chatRes.data
    modelVersions.value = modelRes.data
  } finally {
    logsLoading.value = false
  }
}

watch(activeTab, (tab) => {
  if (tab === 'analytics' && !analytics.value) loadAnalytics()
  if (tab === 'donors') loadDonors()
  if (tab === 'system') loadSystemLogs()
})

watch(statusFilter, loadDonors)

onMounted(loadAnalytics)
</script>

<style scoped>
.tabs { display: flex; gap: 0; margin-bottom: 32px; border: 2px solid #000; border-radius: 4px; overflow: hidden; width: fit-content; box-shadow: var(--shadow-sm); }
.tab-btn {
  padding: 10px 22px; border: none; background: #fff; font-size: 13px;
  font-weight: 700; cursor: pointer; color: var(--text-muted);
  border-right: 2px solid #000;
  transition: var(--transition); font-family: var(--font); letter-spacing: 0.02em;
}
.tab-btn:last-child { border-right: none; }
.tab-btn.active { background: var(--accent); color: #000; }
.tab-btn:hover:not(.active) { background: var(--bg-subtle); color: var(--text); }
.table-wrapper { overflow-x: auto; }
.filter-select {
  padding: 9px 14px; border: 2px solid #000;
  border-radius: 4px; font-size: 13px; font-family: var(--font);
  color: var(--text); background: #fff; outline: none;
  box-shadow: 2px 2px 0 #000; transition: transform var(--transition), box-shadow var(--transition);
}
.filter-select:focus { box-shadow: 3px 3px 0 #000; }
.action-btns { display: flex; gap: 6px; }
.ml-status-box {
  display: flex; align-items: center; gap: 22px;
  padding: 22px 26px; background: #fff;
  border: 2px solid #000; border-radius: 6px; margin-bottom: 24px;
  box-shadow: var(--shadow-md);
}
.ml-status-icon { font-size: 44px; flex-shrink: 0; }
.ml-status-text { font-size: 17px; font-weight: 800; margin-bottom: 4px; color: var(--text); }
.ml-last { font-size: 13px; color: var(--text-muted); font-weight: 500; }
.ml-note { margin-top: 18px; font-size: 13px; color: var(--text-muted); line-height: 1.6; font-weight: 500; }

.truncate { max-width: 150px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.table-sm th, .table-sm td { padding: 8px 12px; font-size: 12px; }
</style>
