<template>
  <div class="page">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">ML Analytics Dashboard</h1>
          <p class="page-subtitle">Organ demand forecasts, ODII scores and explainable AI insights — powered by real
            survey data</p>
        </div>
        <button class="btn btn-ghost btn-sm" @click="loadData" :disabled="loading">↺ Refresh</button>
      </div>

      <div v-if="loading" class="spinner-wrap">
        <div class="spinner"></div>
      </div>

      <template v-else>
        <!-- Metrics cards -->
        <div class="grid-4" style="margin-bottom:32px; gap: 5px" v-if="metrics">
          <div class="stat-card">
            <div class="stat-icon">🎯</div>
            <div class="stat-value">{{ metrics.accuracy ? (metrics.accuracy * 100).toFixed(1) + '%' : 'N/A' }}</div>
            <div class="stat-label">Model Accuracy</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📏</div>
            <div class="stat-value">{{ metrics.mae?.toFixed(3) || 'N/A' }}</div>
            <div class="stat-label">Mean Abs Error</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📉</div>
            <div class="stat-value">{{ metrics.rmse?.toFixed(3) || 'N/A' }}</div>
            <div class="stat-label">RMSE</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📐</div>
            <div class="stat-value">{{ metrics.r2_score?.toFixed(3) || 'N/A' }}</div>
            <div class="stat-label">R² Score</div>
          </div>
        </div>

        <!-- No data state -->
        <div v-if="!hasData" class="no-data-big card">
          <div style="font-size:48px;margin-bottom:16px">🤖</div>
          <h3>No ML data yet</h3>
          <p>Go to <router-link to="/admin">Admin Dashboard</router-link> → ML Training tab and trigger training to
            generate forecasts.</p>
        </div>

        <template v-if="hasData">
          <!-- CSV Survey Insights -->
          <div class="card section" style="margin-bottom:28px">
            <div class="card-header">
              <h3>📊 CSV Survey Insights — Real Field Data</h3>
              <span class="badge badge-info">{{ forecast.length }} regions analysed</span>
            </div>
            <p style="font-size:14px;color:var(--text-muted);margin-bottom:22px">
              Insights derived from <strong>55 real survey responses</strong> collected across {{ forecast.length }}
              Indian cities.
              These data points train the XGBoost demand model and power all forecasts.
            </p>
            <div class="grid-3" style="margin-bottom:24px">
              <div class="insight-tile">
                <div class="it-icon">🗺️</div>
                <div class="it-value">{{ forecast.length }}</div>
                <div class="it-label">Cities covered</div>
              </div>
              <div class="insight-tile">
                <div class="it-icon">👥</div>
                <div class="it-value">{{ totalSurveyed }}</div>
                <div class="it-label">Total respondents</div>
              </div>
              <div class="insight-tile it-highlight">
                <div class="it-icon">❤️</div>
                <div class="it-value">{{ avgWillingness }}%</div>
                <div class="it-label">Avg willingness to donate</div>
              </div>
            </div>

            <!-- Top cities by willingness rate -->
            <div
              style="margin-bottom:6px;font-size:13px;font-weight:700;color:var(--text-muted);text-transform:uppercase;letter-spacing:0.06em">
              Top cities by willingness rate</div>
            <div class="willingness-bars">
              <div v-for="r in topCities" :key="r.region" class="wb-row">
                <div class="wb-city">{{ r.region }}</div>
                <div class="wb-bar-wrap">
                  <div class="wb-bar" :style="{ width: (r.willingness_rate * 100).toFixed(0) + '%' }"></div>
                </div>
                <div class="wb-pct">{{ (r.willingness_rate * 100).toFixed(0) }}%</div>
              </div>
            </div>
          </div>

          <!-- Forecast chart -->
          <div class="card" style="margin-bottom:28px">
            <div class="card-header">6-Month Organ Demand Projection (Top Regions)</div>
            <Line v-if="lineChart" :data="lineChart" :options="lineOptions" />
          </div>

          <!-- Regional forecast table -->
          <div class="card" style="margin-bottom:28px">
            <div class="card-header">Regional Forecast Details</div>
            <div class="table-wrapper">
              <table class="table">
                <thead>
                  <tr>
                    <th>Region</th>
                    <th>Total Surveyed</th>
                    <th>Willing Donors</th>
                    <th>Willingness Rate</th>
                    <th>M1 Projection</th>
                    <th>M3 Projection</th>
                    <th>M6 Projection</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="r in forecast.slice(0, 20)" :key="r.region">
                    <td>{{ r.region }}</td>
                    <td>{{ r.total_surveyed }}</td>
                    <td>{{ r.willing_donors }}</td>
                    <td>{{ (r.willingness_rate * 100).toFixed(1) }}%</td>
                    <td>{{ r.monthly_projections?.[0]?.projected_demand || 'N/A' }}</td>
                    <td>{{ r.monthly_projections?.[2]?.projected_demand || 'N/A' }}</td>
                    <td>{{ r.monthly_projections?.[5]?.projected_demand || 'N/A' }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- SHAP -->
          <div class="card" v-if="shap">
            <div class="card-header">SHAP — Feature Importance Explanation</div>
            <div class="shap-meta">
              <span>📊 Based on {{ shap.sample_count }} samples</span>
              <span>🔝 Top features: {{shap.top_features?.map(f => formatFeature(f)).join(', ')}}</span>
            </div>
            <p class="shap-desc">{{ shap.explanation }}</p>
            <div class="shap-bars">
              <div v-for="(val, feat) in shap.feature_importance" :key="feat" class="shap-row">
                <div class="shap-label">{{ formatFeature(feat) }}</div>
                <div class="shap-bar-wrap">
                  <div class="shap-bar" :style="{ width: barWidth(val) + '%' }"></div>
                </div>
                <div class="shap-val">{{ val.toFixed(4) }}</div>
              </div>
            </div>
          </div>

          <!-- Fairness & Ethics -->
          <div class="grid-2" style="margin-top:28px; gap: 10px">
            <div class="card" v-if="fairness">
              <div class="card-header">⚖️ Fairness & Bias Report</div>
              <p class="shap-desc">Model performance parity across protected groups (higher is fairer).</p>
              <div class="table-wrapper">
                <table class="table table-sm">
                  <thead>
                    <tr>
                      <th>Attribute</th>
                      <th>Parity Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    <template v-for="(score, result) in fairness.feature_dominance" :key="score">
                      <tr :title="result" style="cursor:arrow">
                        <td style="font-weight:700;text-transform:capitalize">{{ result.substring(0, 40) }}</td>
                        <td>
                          <div class="parity-wrap">
                            <div class="parity-bar"
                              :style="{ width: ((score * 100) * 1.5 + 4) + '% !important', background: score > 0.8 ? '#48bb78' : '#ed8936' }">
                            </div>
                            <span>{{ (score * 100).toFixed(0) }}%</span>
                          </div>
                        </td>
                      </tr>
                    </template>
                  </tbody>
                </table>
              </div>
            </div>

            <div class="card" v-if="calibration">
              <div class="card-header">🎯 Prediction Reliability</div>
              <p class="shap-desc">How well model probabilities reflect actual outcomes.</p>

              <div class="stat-card" style="margin-top:10px; border:none; box-shadow:none; padding:0">
                <br>
                <div class="stat-value" style="font-size:32px">
                  {{ (calibration.calibration_error * 100).toFixed(1) }}%
                </div>
                <div class="stat-label">Calibration Error (Lower is Better)</div>
              </div>

              <div style="margin-top:12px; font-size:12px; color:var(--text-muted); line-height:1.6">

                <b>📊 Reliability Score:</b> {{ (calibration.reliability_score * 100).toFixed(1) }}% <br>
                <b>📈 Mean Prediction Confidence:</b> {{ calibration.confidence_stats.mean.toFixed(3) }} <br>
                <b>📉 Confidence Spread (Std):</b> {{ calibration.confidence_stats.std.toFixed(3) }}

                <br><br>

                <b>🔎 Interpretation</b>
                <ul style="margin-top:6px; padding-left:18px">
                  <li>Model shows <b>moderate calibration</b> — probability estimates are reasonably reliable but not
                    perfect.</li>
                  <li><b>Lower probability predictions tend to be over-confident</b>, meaning risk may be slightly
                    overestimated.
                  </li>
                  <li><b>Higher probability predictions align well with real outcomes</b>, indicating strong risk
                    discrimination.
                  </li>
                  <li>Model is generally <b>decisive (high mean confidence)</b>, which is useful for prioritization but
                    requires
                    calibration tuning.</li>
                </ul>

                <b>🧠 Practical Takeaway</b>
                <ul style="margin-top:6px; padding-left:18px">
                  <li>Good for ranking and identifying high-risk organ demand cases.</li>
                  <li>Probability values should be calibrated further for safer clinical decision support.</li>
                  <li>Post-training calibration methods like <b>Isotonic Regression or Platt Scaling</b> can improve
                    trust.</li>
                </ul>

              </div>

              <p style="margin-top:18px; font-size:11px; color:var(--text-muted); font-style:italic">
                Note: Calibration is crucial for trust in predictions, especially in high-stakes domains like organ
                demand
                forecasting.
              </p>

            </div>
          </div>
        </template>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { Line } from 'vue-chartjs'
import {
  Chart as ChartJS, CategoryScale, LinearScale, PointElement, LineElement,
  Title, Tooltip, Legend, Filler
} from 'chart.js'
import api from '../services/api.js'

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Title, Tooltip, Legend, Filler)

const loading = ref(true)
const forecast = ref([])
const shap = ref(null)
const metrics = ref(null)
const fairness = ref(null)
const calibration = ref(null)

const hasData = computed(() => forecast.value.length > 0 || !!shap.value || !!fairness.value)
const maxShap = computed(() => shap.value ? Math.max(...Object.values(shap.value.feature_importance)) : 1)

// CSV survey computed props
const totalSurveyed = computed(() => forecast.value.reduce((s, r) => s + (r.total_surveyed || 0), 0))
const avgWillingness = computed(() => {
  if (!forecast.value.length) return 0
  const avg = forecast.value.reduce((s, r) => s + (r.willingness_rate || 0), 0) / forecast.value.length
  return (avg * 100).toFixed(1)
})
const topCities = computed(() =>
  [...forecast.value].sort((a, b) => b.willingness_rate - a.willingness_rate).slice(0, 8)
)

function barWidth(val) {
  return maxShap.value ? (val / maxShap.value) * 100 : 0
}
function formatFeature(f) {
  return f.replace(/_enc$/, '').replace(/_/g, ' ')
}

const lineChart = computed(() => {
  const top5 = forecast.value.slice(0, 5)
  if (!top5.length) return null
  const months = ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6']
  const colors = ['#e53e3e', '#38b2ac', '#ed8936', '#9f7aea', '#4299e1']
  return {
    labels: months,
    datasets: top5.map((r, i) => ({
      label: r.region,
      data: r.monthly_projections?.map(m => m.projected_demand) || [],
      borderColor: colors[i],
      backgroundColor: colors[i] + '20',
      tension: 0.3,
      fill: false,
    })),
  }
})

const lineOptions = {
  responsive: true,
  plugins: { legend: { position: 'bottom' } },
  scales: { y: { beginAtZero: true } },
}

async function loadData() {
  loading.value = true
  try {
    const [forecastRes, shapRes, metricsRes, fairnessRes, calibrationRes] = await Promise.allSettled([
      api.get('/ml/predict'),
      api.get('/ml/explain'),
      api.get('/ml/metrics'),
      api.get('/ml/fairness'),
      api.get('/ml/calibration'),
    ])
    if (forecastRes.status === 'fulfilled') forecast.value = forecastRes.value.data.forecast || []
    if (shapRes.status === 'fulfilled') shap.value = shapRes.value.data
    if (metricsRes.status === 'fulfilled') metrics.value = metricsRes.value.data
    if (fairnessRes.status === 'fulfilled') fairness.value = fairnessRes.value.data
    if (calibrationRes.status === 'fulfilled') calibration.value = calibrationRes.value.data
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<style scoped>
/* Insight tiles */
.insight-tile {
  background: #fff;
  border: 2px solid #000;
  border-radius: 6px;
  padding: 20px;
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.insight-tile.it-highlight {
  background: var(--primary-light);
  border-color: #000;
  box-shadow: var(--shadow-red);
}

.it-icon {
  font-size: 26px;
  margin-bottom: 8px;
}

.it-value {
  font-size: 28px;
  font-weight: 900;
  color: var(--primary);
  letter-spacing: -0.02em;
}

.it-highlight .it-value {
  color: var(--primary);
}

.it-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 700;
  margin-top: 4px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Willingness bars */
.willingness-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.wb-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.wb-city {
  width: 120px;
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  flex-shrink: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.wb-bar-wrap {
  flex: 1;
  background: #e5e7eb;
  border: 1.5px solid #000;
  border-radius: 2px;
  height: 11px;
  overflow: hidden;
}

.wb-bar {
  background: var(--primary);
  height: 100%;
  border-radius: 1px;
  transition: width 0.7s ease;
}

.wb-pct {
  width: 42px;
  font-size: 12px;
  font-weight: 700;
  color: var(--primary);
  text-align: right;
}

.no-data-big {
  text-align: center;
  padding: 80px;
}

.no-data-big h3 {
  font-size: 22px;
  font-weight: 900;
  margin-bottom: 10px;
}

.no-data-big p {
  color: var(--text-muted);
  font-size: 15px;
  font-weight: 500;
}

.no-data-big a {
  color: var(--primary);
  font-weight: 800;
}

.table-wrapper {
  overflow-x: auto;
}

.shap-meta {
  display: flex;
  gap: 24px;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 16px;
  flex-wrap: wrap;
  font-weight: 600;
}

.shap-meta span {
  display: flex;
  align-items: center;
  gap: 6px;
}

.shap-desc {
  font-size: 14px;
  color: var(--text-muted);
  margin-bottom: 22px;
  font-weight: 500;
}

.shap-bars {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.shap-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.shap-label {
  width: 180px;
  font-size: 13px;
  font-weight: 700;
  text-transform: capitalize;
  flex-shrink: 0;
  color: var(--text);
}

.shap-bar-wrap {
  flex: 1;
  background: #e5e7eb;
  border: 1.5px solid #000;
  border-radius: 2px;
  height: 13px;
  overflow: hidden;
}

.shap-bar {
  background: var(--primary);
  height: 100%;
  border-radius: 1px;
  transition: width 0.7s ease;
}

.shap-val {
  width: 64px;
  font-size: 12px;
  font-weight: 700;
  color: var(--text-muted);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

/* Fairness styles */
.parity-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
}

.parity-bar {
  height: 8px;
  border-radius: 4px;
  border: 1px solid #000;
  max-width: 60px;
}

.table-sm th,
.table-sm td {
  padding: 8px 12px;
  font-size: 12px;
}
</style>
