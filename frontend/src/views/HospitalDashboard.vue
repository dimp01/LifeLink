<template>
  <!--aside :class="['sidebar', { open: sidebarOpen }]">

      <nav class="nav">
        <a class="nav-item active">Dashboard</a>
        <a class="nav-item">Live Organ Queue</a>
        <a class="nav-item">AI Match Engine</a>
        <a class="nav-item">Geo Matching</a>
        <a class="nav-item">Waitlist</a>
        <a class="nav-item">Logistics</a>
        <a class="nav-item">Hospital Capacity</a>
        <a class="nav-item">AI Explainability</a>
        <a class="nav-item">Reports</a>
        <a class="nav-item">Settings</a>
      </nav>

      <div class="ai-status">
        <div class="dot"></div>
        AI Engine Active
      </div>

    </aside-->

  <div class="page">
    <div class="container">

      <!-- HEADER -->
      <header class="header">
        <button class="menu-btn" @click="sidebarOpen = !sidebarOpen">☰</button>

        <input class="search" placeholder="Search recipient / donor ID..." />

        <div class="header-right">
          🔔
          👨‍⚕️
        </div>
      </header>

      <h1 class="page-title">Hospital Analytics Dashboard</h1>
      <p class="page-subtitle">Organ demand forecasts and regional instability insights</p>

      <div v-if="loading" class="spinner"></div>

      <template v-else>
        <!-- Stats -->
        <div class="grid-4" style="margin-top:32px;margin-bottom:28px;gap: 10px">
          <div class="stat-card" v-for="s in stats" :key="s.label">
            <div class="stat-icon">{{ s.icon }}</div>
            <div class="stat-value">{{ s.value }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </div>
        </div>

        <!-- Charts row -->
        <div class="grid-2" style="margin-bottom:28px">
          <div class="card">
            <div class="card-header">Regional Demand Forecast</div>
            <Bar v-if="forecastChart" :data="forecastChart" :options="chartOptions" />
            <div v-else class="no-data">No forecast data. Trigger ML training.</div>
          </div>
          <div class="card">
            <div class="card-header">ODII by Organ Type</div>
            <Bar v-if="odiiChart" :data="odiiChart" :options="chartOptions" />
            <div v-else class="no-data">No ODII data available.</div>
          </div>
        </div>

        <!-- ODII Table -->
        <div class="card" style="margin-bottom:28px">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
            <span>Organ Demand Instability Index (ODII)</span>
            <div class="filter-row">
              <select v-model="selectedOrgan" class="filter-select">
                <option value="">All Organs</option>
                <option v-for="o in organs" :key="o" :value="o">{{ o }}</option>
              </select>
            </div>
          </div>
          <div class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Organ</th>
                  <th>Projected Demand</th>
                  <th>Supply</th>
                  <th>Donors</th>
                  <th>ODII</th>
                  <th>Confidence</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="row in filteredOdii" :key="row.region + row.organ_type">
                  <td>{{ row.region }}</td>
                  <td>{{ row.organ_type }}</td>
                  <td>{{ row.projected_demand }}</td>
                  <td>{{ row.available_supply }}</td>
                  <td>{{ row.registered_donors }}</td>
                  <td><strong>{{ row.instability_index }}</strong></td>
                  <td>{{ (row.confidence_score * 100).toFixed(0) }}%</td>
                  <td>
                    <span class="badge" :class="riskClass(row.instability_index)">
                      {{ riskLabel(row.instability_index) }}
                    </span>
                  </td>
                </tr>
                <tr v-if="filteredOdii.length === 0">
                  <td colspan="8" style="text-align:center;color:var(--text-muted)">No data available</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- SHAP Explanations -->
        <div class="card">
          <div class="card-header">AI Explanation (SHAP Feature Importance)</div>
          <div v-if="shap" class="shap-section">
            <p class="shap-desc">{{ shap.explanation }}</p>
            <div class="shap-bars">
              <div v-for="(val, feat) in shap.feature_importance" :key="feat" class="shap-row">
                <div class="shap-label">{{ formatFeature(feat) }}</div>
                <div class="shap-bar-wrap">
                  <div class="shap-bar" :style="{ width: barWidth(val, shap.feature_importance) + '%' }"></div>
                </div>
                <div class="shap-val">{{ val.toFixed(4) }}</div>
              </div>
            </div>
          </div>
          <div v-else class="no-data">No SHAP data. Run ML training first.</div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend
} from 'chart.js'
import api from '../services/api.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const loading = ref(true)
const odiiData = ref([])
const forecastData = ref([])
const shap = ref(null)
const metrics = ref(null)
const selectedOrgan = ref('')
const organs = ['Kidney', 'Liver', 'Heart', 'Lungs', 'Eyes', 'Cornea', 'Pancreas', 'Intestine', 'Skin', 'Bone Marrow']

const chartOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } },
}

const stats = computed(() => [
  { icon: '🗺️', label: 'Regions Monitored', value: [...new Set(odiiData.value.map(d => d.region))].length },
  { icon: '📊', label: 'Avg ODII', value: odiiData.value.length ? (odiiData.value.reduce((a, b) => a + b.instability_index, 0) / odiiData.value.length).toFixed(3) : 'N/A' },
  { icon: '⚠️', label: 'High Risk Zones', value: odiiData.value.filter(d => d.instability_index > 0.5).length },
  { icon: '🎯', label: 'Model Accuracy', value: metrics.value ? (metrics.value.accuracy * 100).toFixed(1) + '%' : 'N/A' },
])

const filteredOdii = computed(() => {
  if (!selectedOrgan.value) return odiiData.value.slice(0, 50)
  return odiiData.value.filter(d => d.organ_type === selectedOrgan.value).slice(0, 50)
})

const forecastChart = computed(() => {
  if (!forecastData.value.length) return null
  const top10 = forecastData.value.slice(0, 10)
  return {
    labels: top10.map(d => d.region),
    datasets: [{
      label: 'Willingness Rate',
      data: top10.map(d => (d.willingness_rate * 100).toFixed(1)),
      backgroundColor: '#e53e3e',
    }],
  }
})

const odiiChart = computed(() => {
  if (!odiiData.value.length) return null
  const byOrgan = {}
  odiiData.value.forEach(d => {
    if (!byOrgan[d.organ_type]) byOrgan[d.organ_type] = []
    byOrgan[d.organ_type].push(d.instability_index)
  })
  const labels = Object.keys(byOrgan)
  const data = labels.map(o => (byOrgan[o].reduce((a, b) => a + b, 0) / byOrgan[o].length).toFixed(3))
  return {
    labels,
    datasets: [{ label: 'Avg ODII', data, backgroundColor: '#38b2ac' }],
  }
})

function riskClass(v) {
  if (v > 0.5) return 'badge-danger'
  if (v > 0.2) return 'badge-warning'
  return 'badge-success'
}
function riskLabel(v) {
  if (v > 0.5) return 'High'
  if (v > 0.2) return 'Medium'
  return 'Low'
}
function formatFeature(f) {
  return f.replace(/_enc$/, '').replace(/_/g, ' ')
}
function barWidth(val, obj) {
  const max = Math.max(...Object.values(obj))
  return max ? (val / max) * 100 : 0
}

async function loadData() {
  loading.value = true
  try {
    const [odiiRes, forecastRes, shapRes, metricsRes] = await Promise.allSettled([
      api.get('/ml/instability-index'),
      api.get('/ml/predict'),
      api.get('/ml/explain'),
      api.get('/ml/metrics'),
    ])
    if (odiiRes.status === 'fulfilled') odiiData.value = odiiRes.value.data.data || []
    if (forecastRes.status === 'fulfilled') forecastData.value = forecastRes.value.data.forecast || []
    if (shapRes.status === 'fulfilled') shap.value = shapRes.value.data
    if (metricsRes.status === 'fulfilled') metrics.value = metricsRes.value.data
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
.table-wrapper { overflow-x: auto; }
.no-data { text-align: center; color: var(--text-muted); padding: 48px; font-size: 15px; font-weight: 600; }
.filter-row { display: flex; gap: 10px; flex-wrap: wrap; }
.filter-select {
  padding: 9px 14px; border: 2px solid #000;
  border-radius: 4px; font-size: 13px; font-family: var(--font); color: var(--text);
  background: #fff; outline: none;
  box-shadow: 2px 2px 0 #000; transition: transform var(--transition), box-shadow var(--transition);
}
.filter-select:focus { box-shadow: 3px 3px 0 #000; }
.shap-section { padding: 10px 0; }
.shap-desc { font-size: 14px; color: var(--text-muted); margin-bottom: 22px; line-height: 1.6; font-weight: 500; }
.shap-bars { display: flex; flex-direction: column; gap: 14px; }
.shap-row { display: flex; align-items: center; gap: 14px; }
.shap-label { width: 180px; font-size: 13px; font-weight: 700; text-transform: capitalize; flex-shrink: 0; color: var(--text); }
.shap-bar-wrap { flex: 1; background: #e5e7eb; border: 1.5px solid #000; border-radius: 2px; height: 13px; overflow: hidden; }
.shap-bar { background: var(--primary); height: 100%; border-radius: 1px; transition: width 0.6s ease; }
.shap-val { width: 64px; font-size: 12px; font-weight: 700; color: var(--text-muted); text-align: right; }
.sidebar {
  width: 260px;
  background: #111827;
  color: white;
  padding: 24px 18px;
  position: sticky;
  top: 0;
  height: 100vh;
  transition: 0.3s;
}

.logo {
  font-size: 20px;
  font-weight: 800;
  margin-bottom: 30px;
}

.nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.nav-item {
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.nav-item:hover {
  background: #1f2937;
}

.nav-item.active {
  background: #ef4444;
}

/* AI STATUS */
.ai-status {
  margin-top: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 40px;
  font-size: 13px;
}

.dot {
  width: 10px;
  height: 10px;
  background: #22c55e;
  border-radius: 50%;
}

/* MAIN */
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

/* HEADER */
.header {
  height: 70px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 20px;
}

.menu-btn {
  display: none;
}

.search {
  flex: 1;
  padding: 10px 14px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
}

.header-right {
  display: flex;
  gap: 20px;
  font-size: 20px;
}

/* CONTENT */
.content {
  padding: 28px;
}

/* RESPONSIVE */
@media (max-width: 900px) {
  .sidebar {
    position: fixed;
    left: -260px;
    z-index: 999;
  }

  .sidebar.open {
    left: 0;
  }

  .menu-btn {
    display: block;
  }
}
</style>
