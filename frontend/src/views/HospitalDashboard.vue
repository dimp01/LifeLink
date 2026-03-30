<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title">Hospital Operations Dashboard</h1>
      <p class="page-subtitle">Analytics, donor and recipient management, and smart matching workflows</p>

      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          :disabled="requiresHospitalOnboarding && tab.id !== 'verification'"
          @click="activeTab = tab.id"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <div v-if="activeTab === 'verification' && isHospitalUser">
        <div class="card" style="margin-bottom: 20px;">
          <div class="card-header">Hospital Registration & Verification</div>

          <div v-if="onboardingLoading" class="spinner"></div>

          <template v-else>
            <div v-if="onboardingError" class="alert alert-error">{{ onboardingError }}</div>
            <div v-if="onboardingSuccess" class="alert alert-success">{{ onboardingSuccess }}</div>

            <div v-if="isVerificationPending" class="alert alert-info">
              Profile submitted successfully. Your hospital verification is pending admin approval.
            </div>

            <div v-if="hospitalProfile?.is_verified" class="alert alert-success">
              Your hospital account is verified. You can now use all dashboard features.
            </div>

            <form @submit.prevent="submitHospitalRegistration" v-if="!hospitalProfile?.is_verified">
              <div class="form-row">
                <div class="form-group"><label>Hospital Name</label><input v-model="onboardingForm.hospital_name" required /></div>
                <div class="form-group"><label>Registration Number</label><input v-model="onboardingForm.registration_number" required /></div>
                <div class="form-group"><label>City</label><input v-model="onboardingForm.city" required /></div>
                <div class="form-group"><label>State</label><input v-model="onboardingForm.state" required /></div>
              </div>

              <div class="form-row">
                <div class="form-group"><label>Phone</label><input v-model="onboardingForm.phone" /></div>
                <div class="form-group"><label>Email</label><input v-model="onboardingForm.email" type="email" /></div>
                <div class="form-group"><label>Website</label><input v-model="onboardingForm.website" placeholder="https://" /></div>
                <div class="form-group"><label>Bed Capacity</label><input v-model.number="onboardingForm.bed_capacity" type="number" min="0" /></div>
              </div>

              <div class="form-row">
                <div class="form-group full-row"><label>Specializations</label>
                  <div class="checkbox-group">
                    <label v-for="o in organs" :key="`spec-${o}`"><input type="checkbox" :value="o" v-model="onboardingForm.specializations" /> {{ o }}</label>
                  </div>
                </div>
              </div>

              <button class="btn btn-primary" :disabled="onboardingSaving">
                {{ onboardingSaving ? 'Submitting...' : 'Submit for Verification' }}
              </button>
            </form>
          </template>
        </div>
      </div>

      <div v-if="activeTab === 'analytics'">
        <div v-if="analyticsLoading" class="spinner"></div>
        <template v-else>
          <div class="grid-4" style="margin-bottom: 24px; gap: 12px;">
            <div class="stat-card" v-for="s in stats" :key="s.label">
              <div class="stat-icon">{{ s.icon }}</div>
              <div class="stat-value">{{ s.value }}</div>
              <div class="stat-label">{{ s.label }}</div>
            </div>
          </div>

          <div class="grid-2" style="margin-bottom: 24px; gap: 16px;">
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

          <div class="card" style="margin-bottom: 24px;">
            <div class="card-header" style="display:flex;justify-content:space-between;align-items:center">
              <span>Organ Demand Instability Index (ODII)</span>
              <select v-model="selectedOrgan" class="filter-select">
                <option value="">All Organs</option>
                <option v-for="o in organs" :key="o" :value="o">{{ o }}</option>
              </select>
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

          <div class="grid-2" style="gap: 16px;">
            <div class="card">
              <div class="card-header">AI Explanation (SHAP)</div>
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

            <div class="card">
              <div class="card-header">Suggested Next Actions</div>
              <div class="suggestion-list">
                <div class="suggestion-item" v-for="item in smartSuggestions" :key="item.title">
                  <div class="suggestion-title">{{ item.title }}</div>
                  <div class="suggestion-body">{{ item.body }}</div>
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>

      <div v-if="activeTab === 'donors'">
        <div class="card" style="margin-bottom: 24px;">
          <div class="card-header">Add Donor</div>
          <div v-if="donorMsg" :class="['alert', donorError ? 'alert-error' : 'alert-success']">{{ donorMsg }}</div>
          <form @submit.prevent="addDonor">
            <div class="form-row">
              <div class="form-group"><label>Full Name</label><input v-model="donorForm.full_name" required /></div>
              <div class="form-group"><label>Age</label><input v-model.number="donorForm.age" type="number" min="18" max="75" required /></div>
              <div class="form-group"><label>Blood Group</label>
                <select v-model="donorForm.blood_group" required>
                  <option value="" disabled>Select</option>
                  <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
                </select>
              </div>
              <div class="form-group"><label>Location</label><input v-model="donorForm.location" required /></div>
            </div>
            <div class="form-row">
              <div class="form-group full-row"><label>Organs</label>
                <div class="checkbox-group">
                  <label v-for="o in organs" :key="`d-${o}`"><input type="checkbox" :value="o" v-model="donorForm.organs_selected" /> {{ o }}</label>
                </div>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group"><label>Emergency Contact</label><input v-model="donorForm.emergency_contact" /></div>
              <div class="form-group"><label>Medical History</label><textarea rows="2" v-model="donorForm.medical_history"></textarea></div>
            </div>
            <button class="btn btn-primary" :disabled="donorSubmitting">{{ donorSubmitting ? 'Adding...' : 'Add Donor' }}</button>
          </form>
        </div>

        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <span>Donor Directory ({{ donors.length }})</span>
            <div class="filter-row">
              <select v-model="donorStatusFilter" class="filter-select">
                <option value="">All Status</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
              <select v-model="donorBloodFilter" class="filter-select">
                <option value="">All Blood Groups</option>
                <option v-for="bg in bloodGroups" :key="`f-${bg}`" :value="bg">{{ bg }}</option>
              </select>
            </div>
          </div>
          <div v-if="donorsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th><th>Age</th><th>Blood</th><th>Location</th><th>Organs</th><th>Donation Mode</th><th>Status</th><th>Registered</th><th>Actions</th>
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
                  <td>
                    <span class="badge" :class="d.donation_mode === 'relative' ? 'badge-neutral' : (d.donation_mode === 'after_death' ? 'badge-warning' : 'badge-success')">
                      {{ d.donation_mode || 'general' }}
                    </span>
                  </td>
                  <td><span class="badge" :class="donorStatusBadge(d.status)">{{ d.status }}</span></td>
                  <td>{{ new Date(d.created_at).toLocaleDateString() }}</td>
                  <td>
                    <button
                      v-if="d.donation_mode === 'after_death' && !d.is_deceased"
                      class="btn btn-sm btn-danger"
                      @click="markDonorDeceased(d)"
                    >Mark Deceased</button>
                    <span v-else-if="d.donation_mode === 'after_death' && d.is_deceased" class="badge badge-danger">Deceased</span>
                    <span v-else class="text-muted">—</span>
                  </td>
                </tr>
                <tr v-if="donors.length === 0"><td colspan="9" style="text-align:center;color:var(--text-muted)">No donors found</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'recipients'">
        <div class="card" style="margin-bottom: 24px;">
          <div class="card-header">Add Recipient</div>
          <div v-if="recipientMsg" :class="['alert', recipientError ? 'alert-error' : 'alert-success']">{{ recipientMsg }}</div>
          <form @submit.prevent="addRecipient">
            <div class="form-row">
              <div class="form-group"><label>Full Name</label><input v-model="recipientForm.full_name" required /></div>
              <div class="form-group"><label>Age</label><input v-model.number="recipientForm.age" type="number" min="10" max="100" required /></div>
              <div class="form-group"><label>Blood Group</label>
                <select v-model="recipientForm.blood_group" required>
                  <option value="" disabled>Select</option>
                  <option v-for="bg in bloodGroups" :key="`r-${bg}`" :value="bg">{{ bg }}</option>
                </select>
              </div>
              <div class="form-group"><label>Urgency</label>
                <select v-model="recipientForm.urgency" required>
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group full-row"><label>Medical Condition</label><textarea rows="2" v-model="recipientForm.medical_condition" required></textarea></div>
            </div>
            <div class="form-row">
              <div class="form-group full-row"><label>Organs Needed</label>
                <div class="checkbox-group">
                  <label v-for="o in organs" :key="`rneed-${o}`"><input type="checkbox" :value="o" v-model="recipientForm.organ_needed" /> {{ o }}</label>
                </div>
              </div>
            </div>
            <button class="btn btn-primary" :disabled="recipientSubmitting">{{ recipientSubmitting ? 'Adding...' : 'Add Recipient' }}</button>
          </form>
        </div>

        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <span>Recipient Queue ({{ recipients.length }})</span>
            <button class="btn btn-outline btn-sm" @click="loadRecipients" :disabled="recipientsLoading">Refresh</button>
          </div>
          <div v-if="recipientsError" class="alert alert-error" style="margin-bottom: 12px;">{{ recipientsError }}</div>
          <div v-if="recipientsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Name</th><th>Age</th><th>Blood</th><th>Organs Needed</th><th>Urgency</th><th>Status</th><th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="r in recipients" :key="r.id">
                  <td>{{ r.full_name }}</td>
                  <td>{{ r.age }}</td>
                  <td>{{ r.blood_group }}</td>
                  <td>
                    <span class="badge badge-info" v-for="o in (r.organ_needed || []).slice(0,2)" :key="o">{{ o }}</span>
                    <span v-if="r.organ_needed?.length > 2" class="badge badge-info">+{{ r.organ_needed.length - 2 }}</span>
                  </td>
                  <td>
                    <select class="filter-select urgency-select" :value="r.urgency" @change="changeUrgency(r, $event.target.value)">
                      <option value="standard">standard</option>
                      <option value="high">high</option>
                      <option value="urgent">urgent</option>
                    </select>
                  </td>
                  <td><span class="badge badge-warning">{{ r.status }}</span></td>
                  <td>
                    <button class="btn btn-sm btn-accent" @click="findMatches(r)">🔎 Find Match</button>
                  </td>
                </tr>
                <tr v-if="recipients.length === 0"><td colspan="7" style="text-align:center;color:var(--text-muted)">No recipients found</td></tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'matching' && isHospitalUser">
        <div class="card">
          <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap">
            <span>Recipient-first Matching Queue</span>
            <button class="btn btn-outline btn-sm" @click="loadRecipients" :disabled="recipientsLoading">Refresh</button>
          </div>
          <p class="text-muted" style="margin-bottom: 12px;">Recipients are sorted by urgency (urgent, high, standard). Select a recipient to find donor matches.</p>
          <div v-if="recipientsError" class="alert alert-error" style="margin-bottom: 12px;">{{ recipientsError }}</div>
          <div v-if="recipientsLoading" class="spinner"></div>
          <div v-else class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Priority</th>
                  <th>Name</th>
                  <th>Blood</th>
                  <th>Organs Needed</th>
                  <th>Urgency</th>
                  <th>Status</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(r, idx) in recipientsForMatching" :key="r.id">
                  <td>
                    <span class="badge" :class="urgencyBadgeClass(r.urgency)">#{{ idx + 1 }}</span>
                  </td>
                  <td>{{ r.full_name }}</td>
                  <td>{{ r.blood_group }}</td>
                  <td>
                    <span class="badge badge-info" v-for="o in (r.organ_needed || []).slice(0,2)" :key="`m-${r.id}-${o}`">{{ o }}</span>
                    <span v-if="r.organ_needed?.length > 2" class="badge badge-info">+{{ r.organ_needed.length - 2 }}</span>
                  </td>
                  <td>
                    <span class="badge" :class="urgencyBadgeClass(r.urgency)">{{ r.urgency }}</span>
                  </td>
                  <td><span class="badge badge-warning">{{ r.status }}</span></td>
                  <td>
                    <button class="btn btn-sm btn-accent" @click="findMatches(r)">🔎 Find Donor Match</button>
                  </td>
                </tr>
                <tr v-if="recipientsForMatching.length === 0">
                  <td colspan="7" style="text-align:center;color:var(--text-muted)">No recipients available for matching</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div v-if="matchModal" class="modal-overlay" @click.self="closeMatchModal">
        <div class="modal-dialog modal-lg">
          <div class="modal-header">
            <h3>Match Results: {{ selectedRecipient?.full_name }}</h3>
            <button class="modal-close" @click="closeMatchModal">✕</button>
          </div>
          <div class="modal-body">
            <div v-if="matchLoading" class="spinner"></div>
            <div v-else class="table-wrapper">
              <table class="table table-sm">
                <thead>
                  <tr>
                    <th>Donor</th><th>Blood</th><th>Location</th><th>Organ Matches</th><th>Score</th><th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="m in matchCandidates" :key="m.donor_id">
                    <td>{{ m.donor_name }}</td>
                    <td>{{ m.blood_group }}</td>
                    <td>{{ m.location }}</td>
                    <td>{{ m.organ_match_count }}</td>
                    <td><strong>{{ m.score }}</strong></td>
                    <td>
                      <button class="btn btn-sm btn-accent" :disabled="assigningMatch" @click="assignMatch(m)">
                        {{ assigningMatch ? 'Assigning...' : 'Assign Match' }}
                      </button>
                    </td>
                  </tr>
                  <tr v-if="matchCandidates.length === 0"><td colspan="6" style="text-align:center;color:var(--text-muted)">No approved donor matches found</td></tr>
                </tbody>
              </table>
            </div>
            <div v-if="matchAssignMessage" :class="['alert', matchAssignError ? 'alert-error' : 'alert-success']" style="margin-top: 10px;">
              {{ matchAssignMessage }}
            </div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="closeMatchModal">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Bar } from 'vue-chartjs'
import { useAuthStore } from '../stores/auth.js'
import { useRoute } from 'vue-router'
import {
  Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend,
} from 'chart.js'
import api from '../services/api.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

const auth = useAuthStore()
const route = useRoute()
const isHospitalUser = computed(() => auth.role === 'hospital')

const hospitalProfile = ref(null)
const onboardingLoading = ref(false)
const onboardingSaving = ref(false)
const onboardingError = ref('')
const onboardingSuccess = ref('')
const onboardingForm = ref({
  hospital_name: '',
  registration_number: '',
  city: '',
  state: '',
  phone: '',
  email: '',
  website: '',
  bed_capacity: null,
  specializations: [],
})

const isProfileComplete = computed(() => {
  const p = hospitalProfile.value
  return !!(p?.hospital_name && p?.registration_number && p?.city && p?.state)
})

const isVerificationPending = computed(() => {
  if (!hospitalProfile.value) return false
  return isProfileComplete.value && hospitalProfile.value.is_verified === false
})

const requiresHospitalOnboarding = computed(() => {
  if (!isHospitalUser.value) return false
  if (!hospitalProfile.value) return true
  if (!isProfileComplete.value) return true
  return hospitalProfile.value.is_verified === false
})

const activeTab = ref('analytics')
const tabs = computed(() => {
  const baseTabs = []
  if (isHospitalUser.value && (requiresHospitalOnboarding.value || route.query.onboarding === '1')) {
    baseTabs.push({ id: 'verification', label: 'Verification', icon: '✅' })
  }
  baseTabs.push(
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'donors', label: 'Donors', icon: '🩸' },
    { id: 'recipients', label: 'Recipients', icon: '🫁' },
  )
  if (isHospitalUser.value) {
    baseTabs.push({ id: 'matching', label: 'Matching', icon: '🧠' })
  }
  return baseTabs
})

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const organs = ['Kidney', 'Liver', 'Heart', 'Lungs', 'Eyes', 'Cornea', 'Pancreas', 'Intestine', 'Skin', 'Bone Marrow']

// Analytics state
const analyticsLoading = ref(false)
const hospitalStats = ref({ total_recipients: 0, total_organ_requests: 0, urgent_cases: 0, matched_requests: 0 })
const odiiData = ref([])
const forecastData = ref([])
const shap = ref(null)
const metrics = ref(null)
const selectedOrgan = ref('')

// Donor tab state
const donors = ref([])
const donorsLoading = ref(false)
const donorStatusFilter = ref('')
const donorBloodFilter = ref('')
const donorSubmitting = ref(false)
const donorMsg = ref('')
const donorError = ref(false)
const donorForm = ref({
  full_name: '',
  age: null,
  blood_group: '',
  location: '',
  organs_selected: [],
  medical_history: '',
  emergency_contact: '',
})

// Recipient tab state
const recipients = ref([])
const recipientsLoading = ref(false)
const recipientsError = ref('')
const recipientSubmitting = ref(false)
const recipientMsg = ref('')
const recipientError = ref(false)
const recipientForm = ref({
  full_name: '',
  age: null,
  blood_group: '',
  medical_condition: '',
  organ_needed: [],
  urgency: 'standard',
})

// Matches modal
const matchModal = ref(false)
const matchLoading = ref(false)
const selectedRecipient = ref(null)
const matchCandidates = ref([])
const assigningMatch = ref(false)
const matchAssignMessage = ref('')
const matchAssignError = ref(false)

const chartOptions = {
  responsive: true,
  plugins: { legend: { display: false } },
  scales: { y: { beginAtZero: true } },
}

const stats = computed(() => [
  { icon: '🧾', label: 'Total Recipients', value: hospitalStats.value.total_recipients },
  { icon: '🫀', label: 'Organ Requests', value: hospitalStats.value.total_organ_requests },
  { icon: '🚨', label: 'Urgent Cases', value: hospitalStats.value.urgent_cases },
  { icon: '🎯', label: 'Model Accuracy', value: metrics.value?.accuracy ? `${(metrics.value.accuracy * 100).toFixed(1)}%` : 'N/A' },
])

const filteredOdii = computed(() => {
  if (!selectedOrgan.value) return odiiData.value.slice(0, 50)
  return odiiData.value.filter((d) => d.organ_type === selectedOrgan.value).slice(0, 50)
})

const forecastChart = computed(() => {
  if (!forecastData.value.length) return null
  const top10 = forecastData.value.slice(0, 10)
  return {
    labels: top10.map((d) => d.region),
    datasets: [{
      label: 'Willingness Rate',
      data: top10.map((d) => Number((d.willingness_rate * 100).toFixed(1))),
      backgroundColor: '#e53e3e',
    }],
  }
})

const odiiChart = computed(() => {
  if (!odiiData.value.length) return null
  const byOrgan = {}
  odiiData.value.forEach((d) => {
    if (!byOrgan[d.organ_type]) byOrgan[d.organ_type] = []
    byOrgan[d.organ_type].push(d.instability_index)
  })
  const labels = Object.keys(byOrgan)
  const data = labels.map((o) => Number((byOrgan[o].reduce((a, b) => a + b, 0) / byOrgan[o].length).toFixed(3)))
  return {
    labels,
    datasets: [{ label: 'Avg ODII', data, backgroundColor: '#38b2ac' }],
  }
})

const smartSuggestions = computed(() => {
  const urgent = recipients.value.filter((r) => r.urgency === 'urgent').length
  const approvedDonors = donors.value.filter((d) => d.status === 'approved').length
  const pendingDonors = donors.value.filter((d) => d.status === 'pending').length

  const suggestions = [
    {
      title: 'Urgency Prioritization',
      body: urgent > 0
        ? `${urgent} urgent recipient(s) detected. Run Find Match for urgent cases first and escalate logistics.`
        : 'No urgent cases right now. Keep recipients updated to avoid surprise spikes.',
    },
    {
      title: 'Donor Pipeline Health',
      body: pendingDonors > 0
        ? `${pendingDonors} donors are pending approval. Coordinate with admin to speed verification.`
        : 'Pending donor queue is clear. Keep onboarding active to sustain supply.',
    },
    {
      title: 'Match Coverage',
      body: approvedDonors < recipients.value.length
        ? 'Approved donors are fewer than recipients. Launch awareness and targeted donor drives by blood group.'
        : 'Donor supply is healthy relative to recipient volume. Focus on compatibility quality and turnaround time.',
    },
  ]
  return suggestions
})

const urgencyRank = { urgent: 0, high: 1, standard: 2 }

const recipientsForMatching = computed(() => {
  return [...recipients.value].sort((a, b) => {
    const ar = urgencyRank[a.urgency] ?? 3
    const br = urgencyRank[b.urgency] ?? 3
    if (ar !== br) return ar - br
    return new Date(b.created_at) - new Date(a.created_at)
  })
})

async function loadHospitalProfile() {
  if (!isHospitalUser.value) return

  onboardingLoading.value = true
  onboardingError.value = ''
  try {
    const res = await api.get('/hospital/me')
    hospitalProfile.value = res.data
    onboardingForm.value = {
      hospital_name: res.data.hospital_name || '',
      registration_number: res.data.registration_number || '',
      city: res.data.city || '',
      state: res.data.state || '',
      phone: res.data.phone || '',
      email: res.data.email || auth.user?.email || '',
      website: res.data.website || '',
      bed_capacity: res.data.bed_capacity,
      specializations: res.data.specializations || [],
    }
  } catch (e) {
    if (e?.response?.status === 404) {
      hospitalProfile.value = null
      onboardingForm.value.email = auth.user?.email || ''
    } else {
      onboardingError.value = e.response?.data?.detail || 'Unable to load hospital profile.'
    }
  } finally {
    onboardingLoading.value = false
  }
}

async function submitHospitalRegistration() {
  onboardingSaving.value = true
  onboardingError.value = ''
  onboardingSuccess.value = ''

  try {
    const payload = {
      hospital_name: onboardingForm.value.hospital_name,
      registration_number: onboardingForm.value.registration_number,
      city: onboardingForm.value.city,
      state: onboardingForm.value.state,
      phone: onboardingForm.value.phone || null,
      email: onboardingForm.value.email || null,
      website: onboardingForm.value.website || null,
      bed_capacity: onboardingForm.value.bed_capacity,
      specializations: onboardingForm.value.specializations || [],
    }

    await api.post('/hospital/register', payload)
    onboardingSuccess.value = 'Hospital profile submitted. Admin verification is pending.'
    await loadHospitalProfile()
  } catch (e) {
    onboardingError.value = e.response?.data?.detail || 'Unable to submit hospital profile.'
  } finally {
    onboardingSaving.value = false
  }
}

function donorStatusBadge(status) {
  if (status === 'approved') return 'badge-success'
  if (status === 'rejected') return 'badge-danger'
  return 'badge-warning'
}

function urgencyBadgeClass(urgency) {
  if (urgency === 'urgent') return 'badge-danger'
  if (urgency === 'high') return 'badge-warning'
  return 'badge-info'
}

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
  const values = Object.values(obj || {})
  const max = values.length ? Math.max(...values) : 0
  return max ? (val / max) * 100 : 0
}

async function loadAnalytics() {
  analyticsLoading.value = true
  try {
    const [hospitalRes, odiiRes, forecastRes, shapRes, metricsRes] = await Promise.allSettled([
      api.get('/hospital/analytics'),
      api.get('/ml/instability-index'),
      api.get('/ml/predict'),
      api.get('/ml/explain'),
      api.get('/ml/metrics'),
    ])
    if (hospitalRes.status === 'fulfilled') hospitalStats.value = hospitalRes.value.data
    if (odiiRes.status === 'fulfilled') odiiData.value = odiiRes.value.data.data || []
    if (forecastRes.status === 'fulfilled') forecastData.value = forecastRes.value.data.forecast || []
    if (shapRes.status === 'fulfilled') shap.value = shapRes.value.data
    if (metricsRes.status === 'fulfilled') metrics.value = metricsRes.value.data
  } finally {
    analyticsLoading.value = false
  }
}

async function loadDonors() {
  donorsLoading.value = true
  try {
    const params = {}
    if (donorStatusFilter.value) params.status_filter = donorStatusFilter.value
    if (donorBloodFilter.value) params.blood_group = donorBloodFilter.value
    const res = await api.get('/hospital/donors', { params })
    donors.value = res.data
  } finally {
    donorsLoading.value = false
  }
}

async function addDonor() {
  donorSubmitting.value = true
  donorMsg.value = ''
  donorError.value = false
  try {
    await api.post('/hospital/donors', donorForm.value)
    donorMsg.value = 'Donor added successfully.'
    donorForm.value = {
      full_name: '',
      age: null,
      blood_group: '',
      location: '',
      organs_selected: [],
      medical_history: '',
      emergency_contact: '',
    }
    await loadDonors()
    await loadAnalytics()
  } catch (e) {
    donorError.value = true
    donorMsg.value = e.response?.data?.detail || 'Failed to add donor.'
  } finally {
    donorSubmitting.value = false
  }
}

async function loadRecipients() {
  recipientsLoading.value = true
  recipientsError.value = ''
  try {
    const res = await api.get('/hospital/recipients')
    recipients.value = res.data
  } catch (e) {
    recipients.value = []
    recipientsError.value = e?.response?.data?.detail || 'Failed to load recipient profiles.'
  } finally {
    recipientsLoading.value = false
  }
}

async function addRecipient() {
  recipientSubmitting.value = true
  recipientMsg.value = ''
  recipientError.value = false
  try {
    await api.post('/hospital/recipients', recipientForm.value)
    recipientMsg.value = 'Recipient added successfully.'
    recipientForm.value = {
      full_name: '',
      age: null,
      blood_group: '',
      medical_condition: '',
      organ_needed: [],
      urgency: 'standard',
    }
    await loadRecipients()
    await loadAnalytics()
  } catch (e) {
    recipientError.value = true
    recipientMsg.value = e.response?.data?.detail || 'Failed to add recipient.'
  } finally {
    recipientSubmitting.value = false
  }
}

async function changeUrgency(recipient, urgency) {
  try {
    await api.patch(`/hospital/recipients/${recipient.id}/urgency`, null, { params: { urgency } })
    recipient.urgency = urgency
    await loadAnalytics()
  } catch (e) {
    alert(e.response?.data?.detail || 'Unable to update urgency')
  }
}

async function findMatches(recipient) {
  selectedRecipient.value = recipient
  matchModal.value = true
  matchLoading.value = true
  matchCandidates.value = []
  matchAssignMessage.value = ''
  matchAssignError.value = false
  try {
    const res = await api.get(`/hospital/matches/${recipient.id}`)
    matchCandidates.value = res.data
  } catch (e) {
    alert(e.response?.data?.detail || 'Unable to fetch matches')
  } finally {
    matchLoading.value = false
  }
}

async function assignMatch(candidate) {
  if (!selectedRecipient.value) return
  assigningMatch.value = true
  matchAssignMessage.value = ''
  matchAssignError.value = false
  try {
    await api.post('/hospital/matches/assign', {
      donor_id: candidate.donor_id,
      recipient_id: selectedRecipient.value.id,
      notes: 'Assigned from hospital dashboard matching',
    })
    matchAssignMessage.value = 'Match assigned successfully. Donor and recipient dashboards will reflect the match.'
    await Promise.all([loadRecipients(), loadDonors(), loadAnalytics()])
  } catch (e) {
    matchAssignError.value = true
    matchAssignMessage.value = e?.response?.data?.detail || 'Failed to assign match.'
  } finally {
    assigningMatch.value = false
  }
}

async function markDonorDeceased(donor) {
  const ok = window.confirm(`Mark donor ${donor.full_name} as deceased and available for after-death allocation?`)
  if (!ok) return
  try {
    await api.patch(`/hospital/donors/${donor.id}/death`, { is_deceased: true })
    await loadDonors()
  } catch (e) {
    alert(e?.response?.data?.detail || 'Unable to update death status')
  }
}

function closeMatchModal() {
  matchModal.value = false
  selectedRecipient.value = null
  matchCandidates.value = []
  matchAssignMessage.value = ''
  matchAssignError.value = false
}

watch(activeTab, (tab) => {
  if (tab === 'verification') loadHospitalProfile()
  if (tab === 'analytics') loadAnalytics()
  if (tab === 'donors') loadDonors()
  if (tab === 'recipients') loadRecipients()
  if (tab === 'matching' && donors.value.length === 0) loadDonors()
})

watch([donorStatusFilter, donorBloodFilter], () => {
  if (activeTab.value === 'donors') loadDonors()
})

onMounted(async () => {
  await loadHospitalProfile()
  if (isHospitalUser.value && (route.query.onboarding === '1' || requiresHospitalOnboarding.value)) {
    activeTab.value = 'verification'
  }
  await Promise.all([loadAnalytics(), loadDonors(), loadRecipients()])
})
</script>

<style scoped>
.tabs {
  display: flex;
  gap: 0;
  margin: 24px 0;
  border: 2px solid #000;
  border-radius: 4px;
  overflow: hidden;
  width: fit-content;
  box-shadow: var(--shadow-sm);
}

.tab-btn {
  padding: 10px 22px;
  border: none;
  background: #fff;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  color: var(--text-muted);
  border-right: 2px solid #000;
  transition: var(--transition);
  font-family: var(--font);
  letter-spacing: 0.02em;
}

.tab-btn:last-child { border-right: none; }
.tab-btn.active { background: var(--accent); color: #000; }
.tab-btn:hover:not(.active) { background: var(--bg-subtle); color: var(--text); }
.tab-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.table-wrapper { overflow-x: auto; }

.filter-row { display: flex; gap: 8px; flex-wrap: wrap; }

.filter-select {
  padding: 9px 14px;
  border: 2px solid #000;
  border-radius: 4px;
  font-size: 13px;
  font-family: var(--font);
  color: var(--text);
  background: #fff;
  outline: none;
  box-shadow: 2px 2px 0 #000;
  transition: transform var(--transition), box-shadow var(--transition);
}

.filter-select:focus { box-shadow: 3px 3px 0 #000; }

.urgency-select {
  min-width: 110px;
  padding: 6px 10px;
  font-size: 12px;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 14px;
  margin-bottom: 14px;
}

.full-row { grid-column: 1 / -1; }

.checkbox-group {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-top: 8px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-weight: 500;
}

.no-data {
  text-align: center;
  color: var(--text-muted);
  padding: 36px;
  font-size: 14px;
  font-weight: 600;
}

.shap-section { padding: 10px 0; }
.shap-desc { font-size: 14px; color: var(--text-muted); margin-bottom: 18px; line-height: 1.55; font-weight: 500; }
.shap-bars { display: flex; flex-direction: column; gap: 12px; }
.shap-row { display: flex; align-items: center; gap: 12px; }
.shap-label { width: 170px; font-size: 12px; font-weight: 700; text-transform: capitalize; flex-shrink: 0; }
.shap-bar-wrap { flex: 1; background: #e5e7eb; border: 1.5px solid #000; border-radius: 2px; height: 12px; overflow: hidden; }
.shap-bar { background: var(--primary); height: 100%; border-radius: 1px; transition: width 0.5s ease; }
.shap-val { width: 62px; font-size: 12px; font-weight: 700; color: var(--text-muted); text-align: right; }

.suggestion-list { display: flex; flex-direction: column; gap: 12px; }
.suggestion-item { border: 2px solid #000; border-radius: 6px; padding: 12px; background: #fff; box-shadow: var(--shadow-sm); }
.suggestion-title { font-size: 13px; font-weight: 800; margin-bottom: 4px; }
.suggestion-body { font-size: 12px; color: var(--text-muted); line-height: 1.45; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1200;
}

.modal-dialog {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  box-shadow: 0 20px 25px rgba(0, 0, 0, 0.15);
  width: 92%;
  max-width: 720px;
}

.modal-lg { max-width: 920px; }

.modal-header {
  padding: 18px;
  border-bottom: 2px solid #000;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
}

.modal-body { padding: 18px; }

.modal-footer {
  padding: 14px 18px;
  border-top: 2px solid #000;
  display: flex;
  justify-content: flex-end;
}

.table-sm th,
.table-sm td {
  padding: 8px 10px;
  font-size: 12px;
}
</style>
