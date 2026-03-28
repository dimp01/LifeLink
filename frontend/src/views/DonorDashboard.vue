<template>
  <div class="page">
    <div class="container">
      <div class="page-header">
        <div>
          <h1 class="page-title">Donor Dashboard</h1>
          <p class="page-subtitle">Welcome back, {{ auth.user?.full_name }} 👋</p>
        </div>
      </div>

      <!-- Status banner -->
      <div v-if="donor" class="status-banner" :class="'status-' + donor.status">
        <span class="status-icon">{{ statusIcon }}</span>
        <div>
          <strong>Profile Status: {{ donor.status.toUpperCase() }}</strong>
          <p>{{ statusMessage }}</p>
          <p v-if="donor.status === 'rejected' && donor.review_reason" class="review-reason">
            Review note: {{ donor.review_reason }}
          </p>
        </div>
      </div>

      <!-- No profile yet -->
      <div v-if="!donor && !loading && !showForm" class="empty-state">
        <div class="empty-icon">🫀</div>
        <h3>Start your donor pledge in under 2 minutes</h3>
        <p>Begin with essentials first, then complete optional medical details.</p>
        <button class="btn btn-primary btn-lg" @click="startNewRegistration">Start Quick Pledge</button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="spinner"></div>

      <div v-if="loadError && !loading" class="alert alert-error" style="margin-bottom: 16px;">
        {{ loadError }}
        <button class="btn btn-outline btn-sm" style="margin-left: 12px;" @click="loadDashboardData">Retry</button>
      </div>

      <!-- Donor Profile Card -->
      <div v-if="donor && !showForm" class="grid-2" style="margin-top: 24px;">
        <div class="card">
          <div class="card-header">My Donor Profile</div>
          <div class="profile-row" v-for="row in profileRows" :key="row.label">
            <span class="profile-label">{{ row.label }}</span>
            <span class="profile-value">{{ row.value }}</span>
          </div>
          <div class="profile-row">
            <span class="profile-label">Organs</span>
            <div class="organ-tags">
              <span class="badge badge-info" v-for="o in donor.organs_selected" :key="o">{{ o }}</span>
            </div>
          </div>
          <button class="btn btn-outline btn-sm" style="margin-top:16px" @click="startEdit">Edit Profile</button>
        </div>

        <div class="card">
          <div class="card-header">Next Action</div>
          <div class="impact-grid" v-if="completeness">
            <div class="impact-item">
              <div class="impact-icon">📊</div>
              <div class="impact-value">{{ completeness.completion_percent }}%</div>
              <div class="impact-label">Profile completeness</div>
            </div>
            <div class="impact-item">
              <div class="impact-icon">🧭</div>
              <div class="impact-value">{{ completeness.missing_fields.length }}</div>
              <div class="impact-label">Items left</div>
            </div>
          </div>
          <div class="alert alert-info" style="margin-top:16px">
            {{ completeness?.next_action || 'Your pledge has been received and is under review.' }}
          </div>
          <div v-if="completeness?.missing_fields?.length" class="missing-list">
            <div class="profile-label">Missing fields</div>
            <div class="organ-tags" style="margin-top: 8px;">
              <span class="badge" v-for="field in completeness.missing_fields" :key="field">{{ toReadableField(field) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Registration / Edit Form -->
      <div v-if="showForm" class="card form-card">
        <div class="card-header">{{ donor ? 'Update Donor Profile' : 'Quick Pledge Registration' }}</div>

        <div v-if="formError" class="alert alert-error">{{ formError }}</div>

        <div v-if="!donor" class="step-tabs">
          <button type="button" class="step-tab" :class="{ active: formStep === 1 }" @click="formStep = 1">Step 1: Essentials</button>
          <button type="button" class="step-tab" :class="{ active: formStep === 2 }" @click="formStep = 2">Step 2: Additional Details</button>
        </div>

        <form @submit.prevent="submitForm">
          <div class="grid-2" v-if="donor || formStep === 1">
            <div class="form-group">
              <label>Full Name</label>
              <input v-model="form.full_name" type="text" required />
            </div>
            <div class="form-group">
              <label>Age</label>
              <input v-model.number="form.age" type="number" min="1" max="100" required />
            </div>
            <div class="form-group">
              <label>Blood Group</label>
              <select v-model="form.blood_group" required>
                <option v-for="bg in bloodGroups" :key="bg" :value="bg">{{ bg }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>Location (City/State)</label>
              <input v-model="form.location" type="text" required />
            </div>
          </div>

          <div class="form-group" v-if="donor || formStep === 1">
            <label>Organs Willing to Donate</label>
            <div class="organ-checkboxes">
              <label v-for="organ in organList" :key="organ" class="organ-check">
                <input type="checkbox" :value="organ" v-model="form.organs_selected" />
                <span>{{ organ }}</span>
              </label>
            </div>
          </div>

          <div class="form-group" v-if="donor || formStep === 2">
            <label>Medical History (Optional)</label>
            <textarea v-model="form.medical_history" placeholder="Any relevant medical history..."></textarea>
          </div>

          <div class="form-group" v-if="donor || formStep === 2">
            <label>Emergency Contact</label>
            <input v-model="form.emergency_contact" type="text" placeholder="+91 XXXXXXXXXX" />
          </div>

          <div class="form-group consent-group" v-if="donor || formStep === 1">
            <label class="consent-label">
              <input type="checkbox" v-model="form.consent_agreed" :required="!donor" />
              <span>I consent to organ donation and agree to the terms of the Transplantation of Human Organs Act (THOA)</span>
            </label>
          </div>

          <div class="form-actions">
            <button
              v-if="!donor && formStep === 1"
              type="button"
              class="btn btn-primary"
              @click="moveToDetails"
            >
              Continue to Details
            </button>

            <button type="submit" class="btn btn-primary" :disabled="submitting" v-else>
              {{ submitting ? 'Saving...' : (donor ? 'Save Changes' : 'Submit Pledge') }}
            </button>
            <button type="button" class="btn btn-outline" @click="cancelForm">Cancel</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import api from '../services/api.js'

const auth = useAuthStore()
const donor = ref(null)
const loading = ref(false)
const showForm = ref(false)
const submitting = ref(false)
const formError = ref('')
const loadError = ref('')
const formStep = ref(1)
const completeness = ref(null)

const bloodGroups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']
const organList = ['Kidney', 'Liver', 'Heart', 'Lungs', 'Eyes', 'Cornea', 'Pancreas', 'Intestine', 'Skin', 'Bone Marrow']

const form = ref({
  full_name: auth.user?.full_name || '',
  age: '',
  blood_group: 'O+',
  location: '',
  organs_selected: [],
  medical_history: '',
  emergency_contact: '',
  consent_agreed: false,
})

const statusIcon = computed(() => ({ pending: '⏳', approved: '✅', rejected: '❌' }[donor.value?.status] || '❓'))
const statusMessage = computed(() => ({
  pending: 'Your profile is under review by admin. You will be notified once approved.',
  approved: 'Your donor profile is approved! Thank you for your generosity.',
  rejected: 'Your profile was not approved. Please review feedback and update your details.',
}[donor.value?.status] || ''))

const profileRows = computed(() => donor.value ? [
  { label: 'Full Name', value: donor.value.full_name },
  { label: 'Age', value: donor.value.age + ' years' },
  { label: 'Blood Group', value: donor.value.blood_group },
  { label: 'Location', value: donor.value.location },
  { label: 'Emergency Contact', value: donor.value.emergency_contact || 'Not provided' },
  { label: 'Registered On', value: new Date(donor.value.created_at).toLocaleDateString() },
] : [])

async function loadDonor() {
  try {
    loadError.value = ''
    const res = await api.get('/donor/me')
    donor.value = res.data
  } catch (e) {
    if (e.response?.status !== 404) console.error(e)
    if (e.response?.status !== 404) {
      loadError.value = 'Unable to load donor profile right now.'
    }
  }
}

async function loadCompleteness() {
  if (!donor.value) {
    completeness.value = null
    return
  }
  try {
    const res = await api.get('/donor/me/completeness')
    completeness.value = res.data
  } catch (e) {
    console.error(e)
    completeness.value = null
  }
}

async function loadDashboardData() {
  loading.value = true
  try {
    await loadDonor()
    await loadCompleteness()
  } finally {
    loading.value = false
  }
}

function startNewRegistration() {
  formStep.value = 1
  showForm.value = true
}

function startEdit() {
  form.value = {
    full_name: donor.value.full_name,
    age: donor.value.age,
    blood_group: donor.value.blood_group,
    location: donor.value.location,
    organs_selected: [...donor.value.organs_selected],
    medical_history: donor.value.medical_history || '',
    emergency_contact: donor.value.emergency_contact || '',
    consent_agreed: donor.value.consent_agreed || true,
  }
  formStep.value = 2
  showForm.value = true
}

function cancelForm() {
  showForm.value = false
  formStep.value = 1
  formError.value = ''
}

function moveToDetails() {
  formError.value = ''
  if (!form.value.full_name?.trim()) {
    formError.value = 'Please enter your full name.'
    return
  }
  if (!form.value.age || form.value.age < 18 || form.value.age > 75) {
    formError.value = 'Please enter a valid age between 18 and 75.'
    return
  }
  if (!form.value.location?.trim()) {
    formError.value = 'Please enter your location.'
    return
  }
  if (form.value.organs_selected.length === 0) {
    formError.value = 'Please select at least one organ to donate.'
    return
  }
  if (!form.value.consent_agreed) {
    formError.value = 'Consent agreement is required to proceed.'
    return
  }
  formStep.value = 2
}

async function submitForm() {
  if (form.value.organs_selected.length === 0) {
    formError.value = 'Please select at least one organ to donate.'
    return
  }
  submitting.value = true
  formError.value = ''
  try {
    if (donor.value) {
      await api.patch('/donor/me', {
        full_name: form.value.full_name,
        age: form.value.age,
        blood_group: form.value.blood_group,
        location: form.value.location,
        organs_selected: form.value.organs_selected,
        medical_history: form.value.medical_history,
        emergency_contact: form.value.emergency_contact,
      })
    } else {
      await api.post('/donor', form.value)
    }
    await loadDashboardData()
    showForm.value = false
    formStep.value = 1
  } catch (e) {
    formError.value = e.response?.data?.detail || 'Failed to save profile.'
  } finally {
    submitting.value = false
  }
}

function toReadableField(field) {
  const labels = {
    full_name: 'Full Name',
    age: 'Age',
    blood_group: 'Blood Group',
    location: 'Location',
    organs_selected: 'Organs',
    emergency_contact: 'Emergency Contact',
    medical_history: 'Medical History',
    consent_agreed: 'Consent',
  }
  return labels[field] || field
}

onMounted(loadDashboardData)
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 28px; }
.status-banner {
  display: flex; align-items: center; gap: 16px;
  padding: 18px 22px; border-radius: 6px; margin-bottom: 28px;
  border: 2px solid #000; box-shadow: var(--shadow-sm);
}
.status-icon { font-size: 30px; flex-shrink: 0; }
.status-banner strong { font-size: 15px; font-weight: 800; }
.status-banner p { font-size: 13px; opacity: 0.85; margin-top: 3px; font-weight: 500; }
.review-reason { font-weight: 700; color: #7f1d1d; }
.status-pending  { background: #fef9c3; }
.status-approved { background: #dcfce7; }
.status-rejected { background: #fee2e2; }
.empty-state { text-align: center; padding: 80px 0; }
.empty-icon { font-size: 72px; margin-bottom: 20px; }
.empty-state h3 { font-size: 22px; font-weight: 900; margin-bottom: 8px; }
.empty-state p { color: var(--text-muted); margin-bottom: 28px; font-weight: 500; }
.profile-row { display: flex; justify-content: space-between; align-items: center; padding: 12px 0; border-bottom: 2px solid #000; font-size: 14px; }
.profile-row:last-of-type { border-bottom: none; }
.profile-label { color: var(--text-muted); font-weight: 700; text-transform: uppercase; font-size: 11px; letter-spacing: 0.06em; }
.profile-value { font-weight: 700; color: var(--text); }
.organ-tags { display: flex; flex-wrap: wrap; gap: 6px; }
.impact-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 14px; }
.impact-item { text-align: center; padding: 18px; background: #fff; border-radius: 6px; border: 2px solid #000; box-shadow: var(--shadow-sm); }
.impact-icon { font-size: 28px; margin-bottom: 8px; }
.impact-value { font-size: 26px; font-weight: 900; color: var(--primary); letter-spacing: -0.02em; }
.impact-label { font-size: 11px; color: var(--text-muted); margin-top: 3px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; }
.missing-list { margin-top: 12px; }
.form-card { max-width: 820px; margin-top: 28px; }
.step-tabs { display: flex; gap: 10px; margin-bottom: 16px; }
.step-tab {
  border: 2px solid #000;
  background: #fff;
  padding: 8px 14px;
  font-weight: 700;
  cursor: pointer;
  box-shadow: 2px 2px 0 #000;
}
.step-tab.active {
  background: var(--accent);
}
.organ-checkboxes { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 10px; }
.organ-check { display: flex; align-items: center; gap: 9px; font-size: 14px; cursor: pointer; padding: 9px 12px; border: 2px solid #000; border-radius: 4px; transition: var(--transition); box-shadow: 2px 2px 0 #000; font-weight: 600; }
.organ-check:hover { background: var(--accent); transform: translate(-1px,-1px); box-shadow: 3px 3px 0 #000; }
.organ-check input { cursor: pointer; accent-color: var(--primary); }
.consent-group { margin-top: 10px; }
.consent-label { display: flex; align-items: flex-start; gap: 10px; font-size: 14px; cursor: pointer; color: var(--text-soft); font-weight: 500; }
.consent-label input { accent-color: var(--primary); margin-top: 2px; }
.form-actions { display: flex; gap: 12px; margin-top: 28px; }
</style>
