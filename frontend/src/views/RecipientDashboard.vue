<template>
  <div class="dashboard">
    <!-- Header -->
    <header class="dashboard-header">
      <div class="header-content">
        <div>
          <h1>Recipient Dashboard</h1>
          <p class="subtitle">Track your verification and transplant journey</p>
        </div>
        <div class="header-stats">
          <div class="stat-badge" :class="verificationStatusClass">
            <span class="stat-emoji">{{ verificationStatusEmoji }}</span>
            {{ verificationStatusText }}
          </div>
        </div>
      </div>
    </header>

    <!-- Verification Progress Section -->
    <section v-if="recipientProfile" class="verification-section">
      <div class="progress-tracker">
        <h2>Verification Progress</h2>
        <div class="progress-steps">
          <!-- Step 1: Registration -->
          <div class="progress-step" :class="{ completed: recipientProfile.is_verified || recipientProfile.status !== 'not_started', active: recipientProfile.status === 'pending' }">
            <div class="step-indicator">
              <span v-if="recipientProfile.is_verified || recipientProfile.status !== 'not_started'" class="step-icon">✓</span>
              <span v-else class="step-icon">1</span>
            </div>
            <div class="step-content">
              <div class="step-title">Registration Submitted</div>
              <div v-if="recipientProfile.submitted_at" class="step-time">📅 {{ formatDate(recipientProfile.submitted_at) }}</div>
              <div v-else class="step-time">Pending</div>
            </div>
          </div>

          <!-- Progress line -->
          <div class="progress-line" :class="{ completed: recipientProfile.is_verified }"></div>

          <!-- Step 2: Admin Review -->
          <div class="progress-step" :class="{ completed: recipientProfile.is_verified, active: recipientProfile.status === 'pending' }">
            <div class="step-indicator">
              <span v-if="recipientProfile.is_verified" class="step-icon">✓</span>
              <span v-else class="step-icon">2</span>
            </div>
            <div class="step-content">
              <div class="step-title">Admin Review</div>
              <div class="step-time">⏳ In Progress...</div>
            </div>
          </div>

          <!-- Progress line -->
          <div class="progress-line" :class="{ completed: recipientProfile.is_verified }"></div>

          <!-- Step 3: Verified -->
          <div class="progress-step" :class="{ completed: recipientProfile.is_verified }">
            <div class="step-indicator">
              <span v-if="recipientProfile.is_verified" class="step-icon">✓</span>
              <span v-else class="step-icon">3</span>
            </div>
            <div class="step-content">
              <div class="step-title">Verified & Ready</div>
              <div v-if="recipientProfile.verified_at" class="step-time">📅 {{ formatDate(recipientProfile.verified_at) }}</div>
              <div v-else class="step-time">Waiting for verification</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Verification Status Cards -->
      <div class="status-grid">
        <div class="status-card">
          <div class="card-icon">🕐</div>
          <div class="card-content">
            <div class="card-label">Time in Review</div>
            <div class="card-value">{{ timeInReview }}</div>
          </div>
        </div>
        <div class="status-card">
          <div class="card-icon">📋</div>
          <div class="card-content">
            <div class="card-label">Status</div>
            <div class="card-value">{{ capitalizeStatus(recipientProfile.status) }}</div>
          </div>
        </div>
        <div class="status-card">
          <div class="card-icon">⏰</div>
          <div class="card-content">
            <div class="card-label">Estimated ETA</div>
            <div class="card-value">{{ estimatedETA }}</div>
          </div>
        </div>
        <div class="status-card">
          <div class="card-icon">🎯</div>
          <div class="card-content">
            <div class="card-label">Matching Status</div>
            <div class="card-value">{{ matchingStatus }}</div>
          </div>
        </div>
      </div>

      <!-- Alert for Verification Status -->
      <div v-if="!recipientProfile.is_verified && recipientProfile.status === 'pending'" class="alert alert-info">
        <span class="alert-icon">ℹ️</span>
        <div>
          <strong>Verification In Progress</strong>
          <p>Your documents are being reviewed by our admin team. We typically complete reviews within 5-7 business days. You'll receive a notification once your verification is complete.</p>
        </div>
      </div>

      <div v-if="recipientProfile.status === 'rejected'" class="alert alert-danger">
        <span class="alert-icon">❌</span>
        <div>
          <strong>Verification Rejected</strong>
          <p v-if="recipientProfile.reviewer_notes">{{ recipientProfile.reviewer_notes }}</p>
          <p>Please review the feedback and resubmit your information.</p>
          <button class="btn btn-secondary" @click="activeTab = 'resubmit'">Resubmit Application</button>
        </div>
      </div>

      <div v-if="recipientProfile.is_verified" class="alert alert-success">
        <span class="alert-icon">✅</span>
        <div>
          <strong>Verification Complete!</strong>
          <p>Congratulations! Your profile has been verified. You can now be matched with available organs.</p>
        </div>
      </div>

      <div v-if="recipientProfile?.active_match" class="alert alert-success">
        <span class="alert-icon">🎯</span>
        <div>
          <strong>Match Found</strong>
          <p>
            Status: {{ capitalizeStatus(recipientProfile.active_match.status) }}
            <span v-if="recipientProfile.active_match.organ_type"> | Organ: {{ recipientProfile.active_match.organ_type }}</span>
            <span v-if="recipientProfile.active_match.donor_id"> | Donor ID: {{ recipientProfile.active_match.donor_id }}</span>
          </p>
        </div>
      </div>

      <div v-if="recipientProfile.status === 'inactive' || recipientProfile.status === 'cancelled'" class="alert alert-warning">
        <span class="alert-icon">⚠️</span>
        <div>
          <strong>Profile Inactive</strong>
          <p>Your recipient profile is inactive and matching has been stopped.</p>
        </div>
      </div>
    </section>

    <!-- Tabs Section -->
    <section class="tabs-section">
      <div class="tabs">
        <button 
          v-for="tab in availableTabs" 
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.icon }} {{ tab.label }}
        </button>
      </div>

      <!-- Profile Tab -->
      <div v-if="activeTab === 'profile'" class="tab-content">
        <div class="card">
          <div class="card-header">Your Profile Information</div>
          <div v-if="profileLoading" class="spinner"></div>
          <div v-else class="profile-grid">
            <div class="profile-item">
              <label>Full Name</label>
              <p>{{ recipientProfile?.full_name || user.full_name || '—' }}</p>
            </div>
            <div class="profile-item">
              <label>Email</label>
              <p>{{ user.email }}</p>
            </div>
            <div class="profile-item">
              <label>Age</label>
              <p>{{ recipientProfile?.age || '—' }}</p>
            </div>
            <div class="profile-item">
              <label>Blood Group</label>
              <p>{{ recipientProfile?.blood_group || '—' }}</p>
            </div>
            <div class="profile-item">
              <label>Phone</label>
              <p>{{ recipientProfile?.phone || '—' }}</p>
            </div>
            <div class="profile-item">
              <label>Organ Needed</label>
              <p>{{ (recipientProfile?.organ_needed || []).join(', ') || '—' }}</p>
            </div>
            <div class="profile-item">
              <label>Urgency Level</label>
              <p>
                <span class="badge" :class="`badge-${recipientProfile?.urgency || 'standard'}`">
                  {{ capitalizeStatus(recipientProfile?.urgency || 'standard') }}
                </span>
              </p>
            </div>
            <div class="profile-item">
              <label>Status</label>
              <p>{{ capitalizeStatus(recipientProfile?.status || 'pending') }}</p>
            </div>
          </div>
          <button v-if="recipientProfile && !recipientProfile.is_verified" class="btn btn-secondary" style="margin-top: 20px;" @click="activeTab = 'edit'">
            Edit Profile
          </button>

          <div v-if="recipientProfile && recipientProfile.status !== 'inactive'" class="danger-zone">
            <h4>Need to stop verification?</h4>
            <p class="text-muted">You can cancel verification or indicate organ is no longer needed. This will deactivate your account and recipient profile.</p>
            <div class="danger-actions">
              <button class="btn btn-outline-danger" :disabled="deactivationLoading" @click="deactivateRecipient('cancel_verification')">
                {{ deactivationLoading ? 'Processing...' : 'Cancel Verification' }}
              </button>
              <button class="btn btn-danger" :disabled="deactivationLoading" @click="deactivateRecipient('organ_not_needed')">
                {{ deactivationLoading ? 'Processing...' : 'Organ Not Needed' }}
              </button>
            </div>
            <div v-if="deactivationError" class="alert alert-danger" style="margin-top: 12px;">{{ deactivationError }}</div>
            <div v-if="deactivationSuccess" class="alert alert-success" style="margin-top: 12px;">{{ deactivationSuccess }}</div>
          </div>
        </div>
      </div>

      <!-- Edit Profile Tab -->
      <div v-if="activeTab === 'edit'" class="tab-content">
        <div class="card">
          <div class="card-header">Edit Your Profile</div>
          <form @submit.prevent="submitProfile" v-if="!profileLoading">
            <div class="form-row">
              <div class="form-group">
                <label>Full Name *</label>
                <input v-model="profileForm.full_name" type="text" required />
              </div>
              <div class="form-group">
                <label>Age *</label>
                <input v-model.number="profileForm.age" type="number" min="10" max="100" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Blood Group *</label>
                <select v-model="profileForm.blood_group" required>
                  <option value="">Select Blood Group</option>
                  <option value="O+">O+</option>
                  <option value="O-">O-</option>
                  <option value="A+">A+</option>
                  <option value="A-">A-</option>
                  <option value="B+">B+</option>
                  <option value="B-">B-</option>
                  <option value="AB+">AB+</option>
                  <option value="AB-">AB-</option>
                </select>
              </div>
              <div class="form-group">
                <label>Urgency Level *</label>
                <select v-model="profileForm.urgency" required>
                  <option value="standard">Standard</option>
                  <option value="high">High</option>
                  <option value="urgent">Urgent</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Phone *</label>
                <input v-model="profileForm.phone" type="tel" required />
              </div>
              <div class="form-group">
                <label>Address *</label>
                <input v-model="profileForm.address" type="text" required />
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>State</label>
                <select v-model="profileForm.state">
                  <option value="">Select State</option>
                  <option v-for="s in hospitalStates" :key="`r-state-${s}`" :value="s">{{ s }}</option>
                </select>
              </div>
              <div class="form-group">
                <label>City</label>
                <select v-model="profileForm.city">
                  <option value="">Select City</option>
                  <option v-for="c in citiesForSelectedState" :key="`r-city-${c}`" :value="c">{{ c }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group full-row">
                <label>Registered Hospital</label>
                <select v-model="profileForm.hospital_id">
                  <option value="">Select Hospital</option>
                  <option v-for="h in hospitalOptions" :key="h.id" :value="h.id">{{ h.hospital_name }} - {{ h.city }}, {{ h.state }}</option>
                </select>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Medical Condition</label>
                <textarea v-model="profileForm.medical_condition" placeholder="Describe your medical condition..."></textarea>
              </div>
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Organs Needed *</label>
                <div class="checkbox-group">
                  <label><input type="checkbox" value="Kidney" v-model="profileForm.organ_needed"> Kidney</label>
                  <label><input type="checkbox" value="Liver" v-model="profileForm.organ_needed"> Liver</label>
                  <label><input type="checkbox" value="Heart" v-model="profileForm.organ_needed"> Heart</label>
                  <label><input type="checkbox" value="Lungs" v-model="profileForm.organ_needed"> Lungs</label>
                  <label><input type="checkbox" value="Pancreas" v-model="profileForm.organ_needed"> Pancreas</label>
                  <label><input type="checkbox" value="Eyes" v-model="profileForm.organ_needed"> Eyes</label>
                </div>
              </div>
            </div>

            <div v-if="profileError" class="alert alert-danger">{{ profileError }}</div>
            <div v-if="profileSuccess" class="alert alert-success">{{ profileSuccess }}</div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="profileSaving">
                {{ profileSaving ? 'Saving...' : 'Continue to Verification' }}
              </button>
              <button type="button" class="btn btn-outline" @click="activeTab = 'profile'">Cancel</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Verification Tab -->
      <div v-if="activeTab === 'verification'" class="tab-content">
        <div class="card">
          <div class="card-header">
            <span v-if="recipientProfile?.is_verified">✅ Verification Complete</span>
            <span v-else-if="recipientProfile?.status === 'pending'">⏳ Verification In Progress</span>
            <span v-else>📋 Verification Documents</span>
          </div>
          <div v-if="recipientProfile?.is_verified" class="success-message">
            <p>🎉 Your verification has been approved! You can now be matched with available organs.</p>
          </div>

          <div v-if="recipientProfile?.documents && recipientProfile.documents.length > 0" class="documents-list" style="margin-top: 14px;">
            <h3>Submitted Documents</h3>
            <div class="document-group">
              <div v-for="(doc, idx) in recipientProfile.documents" :key="idx" class="document-item">
                <span class="doc-icon">📄</span>
                <div class="doc-info">
                  <div class="doc-name">{{ doc.name || doc.filename }}</div>
                  <div class="doc-meta">{{ formatDate(doc.uploadedAt || doc.uploaded_at) }}</div>
                </div>
                <button type="button" class="btn-action-view" @click="openDocumentModal(doc)">View</button>
              </div>
            </div>
            <p v-if="recipientProfile.verification_notes" class="text-muted">
              <strong>Notes:</strong> {{ recipientProfile.verification_notes }}
            </p>
          </div>

          <div v-if="!recipientProfile?.documents || recipientProfile.documents.length === 0" class="no-verification">
            <p>No verification documents submitted yet.</p>
            <button class="btn btn-primary" @click="activeTab = 'submit-verification'">Submit Verification</button>
          </div>
        </div>
      </div>

      <!-- Submit Verification Tab -->
      <div v-if="activeTab === 'submit-verification' && !recipientProfile?.is_verified" class="tab-content">
        <div class="card">
          <div class="card-header">Submit Verification Documents</div>
          <form @submit.prevent="submitVerification">
            <div v-if="verificationError" class="alert alert-danger">{{ verificationError }}</div>
            <div v-if="verificationSuccess" class="alert alert-success">{{ verificationSuccess }}</div>

            <div class="form-group">
              <label>Additional Notes</label>
              <textarea v-model="verificationForm.notes" placeholder="Any additional information for the admin review..." rows="4"></textarea>
            </div>

            <div class="form-group">
              <label>Upload Documents (Images or PDFs)</label>
              <div class="file-upload" @click="$refs.fileInput.click()">
                <input ref="fileInput" type="file" multiple @change="onFileSelect" accept=".pdf,.jpg,.jpeg,.png" style="display: none;" />
                <p>📤 Click to upload or drag files</p>
                <p style="font-size: 12px; color: #9ca3af;">💡 Upload medical reports, ID proof, and any other relevant documents</p>
              </div>
              <div v-if="verificationForm.documents.length > 0" class="file-list">
                <div v-for="(file, idx) in verificationForm.documents" :key="idx" class="file-item">
                  <span>📎 {{ file.name }}</span>
                  <button type="button" @click="removeFile(idx)" class="btn-remove">✕</button>
                </div>
              </div>
            </div>

            <div class="form-actions">
              <button type="submit" class="btn btn-primary" :disabled="verificationSaving || verificationForm.documents.length === 0">
                {{ verificationSaving ? 'Submitting...' : 'Submit for Verification' }}
              </button>
              <button type="button" class="btn btn-outline" @click="activeTab = 'profile'">Cancel</button>
            </div>
          </form>
        </div>
      </div>

      <!-- Matching Tab -->
      <div v-if="activeTab === 'matching'" class="tab-content">
        <div class="card">
          <div class="card-header">Organ Matching Status</div>
          <div v-if="!recipientProfile?.is_verified" class="alert alert-warning">
            <span class="alert-icon">⚠️</span>
            <strong>Complete verification first</strong> to be eligible for organ matching.
          </div>
          <div v-else class="matching-status">
            <div class="matching-item">
              <div class="organ-badge">🫀</div>
              <div class="organ-info">
                <span class="organ-name">Organs Needed - </span>
                <span class="organ-value">{{ (recipientProfile.organ_needed || []).join(', ') }}</span>
              </div>
            </div>
            <div class="matching-item">
              <div class="organ-badge">📊</div>
              <div class="organ-info">
                <span class="organ-name">Matching Status - </span>
                <span class="organ-value">Searching for matches</span>
              </div>
            </div>
            <p class="text-muted" style="margin-top: 20px;">
              You will receive notifications when a potential match is found. Our system continuously searches for compatible organs.
            </p>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'requests'" class="tab-content">
        <div class="card">
          <div class="card-header">Incoming Match Requests</div>
          <div v-if="matchRequestsLoading" class="spinner"></div>
          <div v-else-if="matchRequests.length === 0" class="alert alert-info">
            No pending match requests right now.
          </div>
          <div v-else>
            <div v-for="req in matchRequests" :key="req.id" class="document-item" style="margin-bottom:10px;">
              <span class="doc-icon">🧬</span>
              <div class="doc-info">
                <div class="doc-name">{{ req.donor_name }} ({{ req.donor_blood_group }})</div>
                <div class="doc-meta">Organs: {{ (req.donor_organs || []).join(', ') || 'N/A' }}</div>
                <div class="doc-meta">Requested: {{ formatDate(req.requested_at) }}</div>
                <div class="doc-meta" v-if="req.message">Message: {{ req.message }}</div>
              </div>
              <div style="display:flex; gap:8px;">
                <button class="btn btn-primary btn-sm" :disabled="requestActionLoading" @click="respondToMatchRequest(req.id, 'accept')">Accept</button>
                <button class="btn btn-outline btn-sm" :disabled="requestActionLoading" @click="respondToMatchRequest(req.id, 'reject')">Reject</button>
              </div>
            </div>
            <div v-if="matchRequestActionError" class="alert alert-danger" style="margin-top: 12px;">{{ matchRequestActionError }}</div>
            <div v-if="matchRequestActionSuccess" class="alert alert-success" style="margin-top: 12px;">{{ matchRequestActionSuccess }}</div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="documentModalOpen" class="doc-modal-overlay" @click.self="closeDocumentModal">
      <div class="doc-modal">
        <div class="doc-modal-header">
          <h3>{{ selectedDocument?.name || selectedDocument?.filename || 'Document Preview' }}</h3>
          <button type="button" class="doc-modal-close" @click="closeDocumentModal">✕</button>
        </div>

        <div class="doc-modal-body">
          <template v-if="selectedDocumentUrl && isImageDocument(selectedDocument)">
            <img :src="selectedDocumentUrl" alt="Submitted document" class="doc-preview-image" />
          </template>

          <template v-else-if="selectedDocumentUrl && isPdfDocument(selectedDocument)">
            <iframe :src="selectedDocumentUrl" class="doc-preview-frame" title="Document PDF Preview"></iframe>
          </template>

          <template v-else-if="selectedDocumentUrl">
            <p class="text-muted">Preview unavailable for this file type.</p>
            <a :href="selectedDocumentUrl" target="_blank" rel="noopener" class="btn btn-primary">Open Document</a>
          </template>

          <template v-else>
            <p class="text-muted">No file URL is available for this document. Only metadata was submitted.</p>
          </template>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'
import api from '../services/api.js'

const auth = useAuthStore()
const user = computed(() => auth.user || {})

const activeTab = ref('profile')
const recipientProfile = ref(null)
const profileLoading = ref(false)
const profileSaving = ref(false)
const profileError = ref('')
const profileSuccess = ref('')

const verificationLoading = ref(false)
const verificationSaving = ref(false)
const verificationError = ref('')
const verificationSuccess = ref('')

const profileForm = ref({
  full_name: '',
  age: null,
  blood_group: '',
  phone: '',
  address: '',
  city: '',
  state: '',
  hospital_id: '',
  medical_condition: '',
  organ_needed: [],
  urgency: 'standard',
})

const verificationForm = ref({
  notes: '',
  documents: [],
})

const documentModalOpen = ref(false)
const selectedDocument = ref(null)
const deactivationLoading = ref(false)
const deactivationError = ref('')
const deactivationSuccess = ref('')
const hospitalOptions = ref([])
const hospitalStates = ref([])
const citiesByState = ref({})
const matchRequests = ref([])
const matchRequestsLoading = ref(false)
const requestActionLoading = ref(false)
const matchRequestActionError = ref('')
const matchRequestActionSuccess = ref('')

const citiesForSelectedState = computed(() => {
  if (!profileForm.value.state) return []
  return citiesByState.value[profileForm.value.state] || []
})

const selectedDocumentUrl = computed(() => {
  const doc = selectedDocument.value
  if (!doc) return ''
  return doc.file_url || doc.url || doc.preview_url || doc.path || ''
})

const availableTabs = computed(() => {
  if (!recipientProfile.value) return []
  const tabs = [
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'verification', label: 'Verification', icon: '📋' },
    { id: 'matching', label: 'Matching', icon: '🎯' },
    { id: 'requests', label: 'Match Requests', icon: '📬' },
  ]
  if (!recipientProfile.value.is_verified && recipientProfile.value.status !== 'verified') {
    tabs.splice(2, 0, { id: 'edit', label: 'Edit Profile', icon: '✏️' })
    if (!recipientProfile.value.documents || recipientProfile.value.documents.length === 0) {
      tabs.splice(3, 0, { id: 'submit-verification', label: 'Submit Verification', icon: '📤' })
    }
  }
  return tabs
})

const verificationStatusText = computed(() => {
  if (!recipientProfile.value) return 'Not Started'
  if (recipientProfile.value.is_verified) return 'Verified'
  if (recipientProfile.value.status === 'pending') return 'Pending Review'
  if (recipientProfile.value.status === 'rejected') return 'Rejected'
  return 'Not Started'
})

const verificationStatusClass = computed(() => {
  if (!recipientProfile.value) return 'status-not-started'
  if (recipientProfile.value.is_verified) return 'status-verified'
  if (recipientProfile.value.status === 'pending') return 'status-pending'
  if (recipientProfile.value.status === 'rejected') return 'status-rejected'
  return 'status-not-started'
})

const verificationStatusEmoji = computed(() => {
  if (!recipientProfile.value) return '❓'
  if (recipientProfile.value.is_verified) return '✅'
  if (recipientProfile.value.status === 'pending') return '⏳'
  if (recipientProfile.value.status === 'rejected') return '❌'
  return '⏳'
})

const timeInReview = computed(() => {
  if (!recipientProfile.value?.submitted_at) return '—'
  const submitted = new Date(recipientProfile.value.submitted_at)
  const now = new Date()
  const days = Math.floor((now - submitted) / (1000 * 60 * 60 * 24))
  const hours = Math.floor(((now - submitted) % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60))
  if (days > 0) return `${days}d ${hours}h`
  return `${hours}h`
})

const estimatedETA = computed(() => {
  if (recipientProfile.value?.is_verified) return 'Complete ✓'
  if (!recipientProfile.value?.submitted_at) return 'TBD'
  const submitted = new Date(recipientProfile.value.submitted_at)
  const estimated = new Date(submitted.getTime() + 7 * 24 * 60 * 60 * 1000)
  return estimated.toLocaleDateString()
})

const matchingStatus = computed(() => {
  if (!recipientProfile.value?.is_verified) return 'Awaiting Verification'
  return 'Active'
})

function capitalizeStatus(str) {
  if (!str) return '—'
  return str.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
}

function formatDate(dateString) {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('en-US', { 
    year: 'numeric', 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

async function loadHospitalDirectory() {
  try {
    const res = await api.get('/hospital/directory')
    hospitalOptions.value = res.data?.hospitals || []
    hospitalStates.value = res.data?.states || []
    citiesByState.value = res.data?.cities_by_state || {}
  } catch (error) {
    hospitalOptions.value = []
    hospitalStates.value = []
    citiesByState.value = {}
  }
}

async function loadRecipientProfile() {
  profileLoading.value = true
  try {
    const response = await api.get('/recipient/me/verification')
    recipientProfile.value = response.data
  } catch (error) {
    const statusCode = error?.response?.status
    if (statusCode !== 404) {
      console.error('Failed to load recipient profile:', error)
      return
    }

    // Backward compatibility for currently deployed API shape.
    try {
      const [profileRes, verificationRes] = await Promise.all([
        api.get('/recipient/profile').catch(() => ({ data: null })),
        api.get('/recipient/verification').catch(() => ({ data: null })),
      ])

      const profile = profileRes?.data
      const verification = verificationRes?.data
      const verificationStatus = verification?.status || 'not_started'
      const profileStatus = profile?.status || 'pending'
      const normalizedStatus = verificationStatus === 'not_started' ? profileStatus : verificationStatus
      const isVerified = ['verified', 'approved', 'matched', 'completed'].includes((profileStatus || '').toLowerCase())

      recipientProfile.value = {
        recipient_id: profile?.id || null,
        is_verified: isVerified,
        status: normalizedStatus,
        submitted_at: verification?.submitted_at || null,
        verified_at: null,
        full_name: profile?.full_name || user.value?.full_name || '',
        age: profile?.age || null,
        blood_group: profile?.blood_group || '',
        phone: null,
        address: null,
        medical_condition: profile?.medical_condition || '',
        organ_needed: profile?.organ_needed || [],
        urgency: profile?.urgency || 'standard',
        documents: [],
        verification_notes: null,
        reviewer_notes: null,
        registered: Boolean(profile?.id),
      }
    } catch (fallbackError) {
      console.error('Failed to load recipient profile:', fallbackError)
      recipientProfile.value = {
        recipient_id: null,
        is_verified: false,
        status: 'not_started',
        submitted_at: null,
        verified_at: null,
        full_name: user.value?.full_name || '',
        age: null,
        blood_group: '',
        phone: null,
        address: null,
        medical_condition: '',
        organ_needed: [],
        urgency: 'standard',
        documents: [],
        verification_notes: null,
        reviewer_notes: null,
        registered: false,
      }
    }
  } finally {
    if (recipientProfile.value) {
      profileForm.value = {
        full_name: recipientProfile.value.full_name || '',
        age: recipientProfile.value.age || null,
        blood_group: recipientProfile.value.blood_group || '',
        phone: recipientProfile.value.phone || '',
        address: recipientProfile.value.address || '',
        city: recipientProfile.value.city || '',
        state: recipientProfile.value.state || '',
        hospital_id: recipientProfile.value.hospital_id || '',
        medical_condition: recipientProfile.value.medical_condition || '',
        organ_needed: recipientProfile.value.organ_needed || [],
        urgency: recipientProfile.value.urgency || 'standard',
      }
    }

    profileLoading.value = false
  }
}

async function submitProfile() {
  profileSaving.value = true
  profileError.value = ''
  profileSuccess.value = ''
  
  try {
    try {
      await api.post('/recipient/register', profileForm.value)
    } catch (error) {
      if (error?.response?.status !== 404) throw error

      // Backward compatibility with older recipient profile endpoint.
      await api.post('/recipient/profile', {
        full_name: profileForm.value.full_name,
        age: profileForm.value.age,
        blood_group: profileForm.value.blood_group,
        medical_condition: profileForm.value.medical_condition,
        organ_needed: profileForm.value.organ_needed,
        urgency: profileForm.value.urgency,
        hospital_id: profileForm.value.hospital_id || null,
      })
    }

    profileSuccess.value = 'Profile submitted successfully! Waiting for verification.'
    await loadRecipientProfile()
    setTimeout(() => {
      activeTab.value = 'submit-verification'
    }, 1500)
  } catch (error) {
    profileError.value = error.response?.data?.detail || 'Failed to save profile'
  } finally {
    profileSaving.value = false
  }
}

function onFileSelect(event) {
  const files = Array.from(event.target.files)
  verificationForm.value.documents = files
}

function removeFile(idx) {
  verificationForm.value.documents.splice(idx, 1)
}

function openDocumentModal(doc) {
  selectedDocument.value = doc || null
  documentModalOpen.value = true
}

function closeDocumentModal() {
  documentModalOpen.value = false
  selectedDocument.value = null
}

function isImageDocument(doc) {
  const type = (doc?.type || doc?.mime_type || '').toLowerCase()
  return type.startsWith('image/')
}

function isPdfDocument(doc) {
  const type = (doc?.type || doc?.mime_type || '').toLowerCase()
  return type.includes('pdf')
}

async function deactivateRecipient(actionType) {
  const reason = actionType === 'organ_not_needed'
    ? 'Organ no longer needed by recipient'
    : 'Recipient requested verification cancellation'

  const ok = window.confirm('This will deactivate your account and recipient profile. Continue?')
  if (!ok) return

  deactivationLoading.value = true
  deactivationError.value = ''
  deactivationSuccess.value = ''

  try {
    await api.post('/recipient/deactivate', { reason })
    deactivationSuccess.value = 'Your account and profile are now inactive. Redirecting to login...'
    recipientProfile.value = {
      ...(recipientProfile.value || {}),
      status: 'inactive',
      is_verified: false,
      profile_is_active: false,
      user_is_active: false,
    }

    setTimeout(() => {
      sessionStorage.removeItem('user')
      sessionStorage.removeItem('access_token')
      window.location.href = '/login'
    }, 1200)
  } catch (error) {
    deactivationError.value = error?.response?.data?.detail || 'Failed to deactivate recipient profile'
  } finally {
    deactivationLoading.value = false
  }
}

async function submitVerification() {
  verificationSaving.value = true
  verificationError.value = ''
  verificationSuccess.value = ''

  try {
    const documents = verificationForm.value.documents.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      uploadedAt: new Date().toISOString(),
    }))

    try {
      await api.post('/recipient/register', {
        full_name: profileForm.value.full_name,
        age: profileForm.value.age,
        blood_group: profileForm.value.blood_group,
        phone: profileForm.value.phone,
        address: profileForm.value.address,
        city: profileForm.value.city || null,
        state: profileForm.value.state || null,
        medical_condition: profileForm.value.medical_condition,
        organ_needed: profileForm.value.organ_needed,
        urgency: profileForm.value.urgency,
        hospital_id: profileForm.value.hospital_id || null,
        verification_notes: verificationForm.value.notes,
        documents: documents,
      })
    } catch (error) {
      if (error?.response?.status !== 404) throw error

      // Fallback to legacy multi-step verification flow.
      await api.post('/recipient/verification/start')
      await api.post('/recipient/verification/step/1', {
        phone: profileForm.value.phone || 'Not provided',
        address: profileForm.value.address || 'Not provided',
        dob: '1990-01-01',
      })
      await api.post('/recipient/verification/step/2', {
        condition: profileForm.value.medical_condition || 'Not provided',
        transplantType: profileForm.value.organ_needed?.[0] || 'Kidney',
        notes: verificationForm.value.notes || null,
      })
      await api.post('/recipient/verification/step/3', {
        documents: {
          uploaded: documents,
        },
      })
      await api.post('/recipient/verification/step/4', {
        name: 'Hospital not assigned',
        contact: 'N/A',
        city: 'N/A',
      })
      await api.post('/recipient/verification/step/5', {
        agreed: true,
        date: new Date().toISOString().slice(0, 10),
      })
      await api.post('/recipient/verification/submit')
    }

    verificationSuccess.value = '✅ Verification submitted successfully! An admin will review your documents soon.'
    await loadRecipientProfile()
    setTimeout(() => {
      activeTab.value = 'verification'
    }, 2000)
  } catch (error) {
    verificationError.value = error.response?.data?.detail || 'Failed to submit verification'
  } finally {
    verificationSaving.value = false
  }
}

async function loadMatchRequests() {
  matchRequestsLoading.value = true
  matchRequestActionError.value = ''
  try {
    const res = await api.get('/recipient/match-requests')
    matchRequests.value = Array.isArray(res.data) ? res.data : []
  } catch (error) {
    matchRequests.value = []
    matchRequestActionError.value = error?.response?.data?.detail || 'Failed to load match requests.'
  } finally {
    matchRequestsLoading.value = false
  }
}

async function respondToMatchRequest(requestId, action) {
  requestActionLoading.value = true
  matchRequestActionError.value = ''
  matchRequestActionSuccess.value = ''
  try {
    await api.post(`/recipient/match-requests/${requestId}/${action}`)
    matchRequestActionSuccess.value = action === 'accept'
      ? 'Request accepted. Your account and donor account are now inactive.'
      : 'Request rejected successfully.'
    await loadMatchRequests()
    await loadRecipientProfile()
    if (action === 'accept') {
      setTimeout(() => {
        sessionStorage.removeItem('user')
        sessionStorage.removeItem('access_token')
        window.location.href = '/login'
      }, 1200)
    }
  } catch (error) {
    matchRequestActionError.value = error?.response?.data?.detail || 'Unable to process request.'
  } finally {
    requestActionLoading.value = false
  }
}

onMounted(() => {
  loadHospitalDirectory()
  loadRecipientProfile()
  loadMatchRequests()
})
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  /* background: var(--bg); */
  /* color: var(--text); */
}

.dashboard-header {
  /* background: var(--primary-dark); */
  /* border-bottom: 2px solid var(--border); */
  padding: 32px 20px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
}

.dashboard-header h1 {
  margin: 0 0 8px 0;
  font-size: 32px;
  font-weight: 900;
}

.subtitle {
  margin: 0;
  color: var(--text-muted);
  font-size: 15px;
}

.header-stats {
  display: flex;
  gap: 12px;
}

.stat-badge {
  padding: 10px 16px;
  border-radius: var(--radius);
  background: var(--bg-subtle);
  border: 2px solid var(--border);
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 8px;
  box-shadow: var(--shadow-sm);
}

.stat-emoji {
  font-size: 18px;
}

.stat-badge.status-verified {
  background: var(--success-bg);
}

.stat-badge.status-pending {
  background: var(--warning-bg);
}

.stat-badge.status-rejected {
  background: var(--danger-bg);
}

.verification-section,
.tabs-section {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
}

.progress-tracker {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow);
  margin-bottom: 20px;
}

.progress-tracker h2 {
  margin: 0 0 20px 0;
  font-size: 20px;
}

.progress-steps {
  display: flex;
  align-items: center;
  gap: 14px;
  overflow-x: auto;
  padding-bottom: 8px;
}

.progress-step {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 220px;
}

.step-indicator {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: var(--bg-subtle);
  border: 2px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  color: var(--text-muted);
}

.progress-step.active .step-indicator {
  background: var(--accent);
  color: var(--text);
}

.progress-step.completed .step-indicator {
  background: var(--success-bg);
  color: var(--success);
}

.step-content {
  flex: 1;
}

.step-title {
  font-weight: 700;
  font-size: 14px;
}

.step-time {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

.progress-line {
  width: 26px;
  height: 2px;
  background: var(--border-soft);
  flex-shrink: 0;
}

.progress-line.completed {
  background: var(--success);
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}

.status-card {
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: var(--shadow-sm);
}

.card-icon {
  font-size: 26px;
}

.card-content {
  flex: 1;
}

.card-label {
  font-size: 11px;
  color: var(--text-muted);
  font-weight: 800;
  text-transform: uppercase;
}

.card-value {
  font-size: 16px;
  font-weight: 800;
}

.alert {
  padding: 14px;
  border-radius: var(--radius);
  border: 2px solid var(--border);
  box-shadow: var(--shadow-sm);
  display: flex;
  gap: 10px;
}

.alert-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  padding: 10px;
  box-shadow: var(--shadow-sm);
  overflow-x: auto;
}

.tab-btn {
  padding: 8px 14px;
  border: 2px solid var(--border);
  background: var(--card-bg);
  cursor: pointer;
  font-weight: 700;
  border-radius: var(--radius-sm);
  white-space: nowrap;
  color: var(--text-muted);
}

.tab-btn:hover {
  background: var(--bg-subtle);
  color: var(--text);
}

.tab-btn.active {
  background: var(--accent);
  color: var(--text);
}

.tab-content {
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.card {
  margin-bottom: 20px;
}

.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: 14px;
}

.profile-item {
  padding: 12px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}

.profile-item label {
  display: block;
  font-size: 11px;
  font-weight: 800;
  color: var(--text-muted);
  text-transform: uppercase;
  margin-bottom: 4px;
}

.profile-item p {
  margin: 0;
  font-size: 14px;
  color: var(--text);
}

.badge-standard {
  background: var(--info-bg);
  color: var(--info);
}

.badge-high {
  background: var(--warning-bg);
  color: var(--warning);
}

.badge-urgent {
  background: var(--danger-bg);
  color: var(--danger);
}

.form-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 16px;
}

.checkbox-group {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 8px;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
}

.file-upload {
  border: 2px dashed var(--border);
  border-radius: var(--radius);
  padding: 24px;
  text-align: center;
  background: var(--bg-subtle);
  cursor: pointer;
}

.file-upload:hover {
  background: var(--accent);
}

.file-list {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  font-size: 13px;
}

.btn-remove {
  background: var(--danger-bg);
  border: 1px solid var(--border);
  color: var(--danger);
  padding: 3px 8px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-weight: 700;
}

.form-actions {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.spinner {
  width: 36px;
  height: 36px;
  border: 4px solid var(--border-soft);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
  margin: 18px auto;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.success-message {
  padding: 14px;
  background: var(--success-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius);
  color: var(--success);
}

.documents-list h3,
.doc-meta,
.no-verification,
.organ-name,
.text-muted {
  color: var(--text-muted);
}

.document-group,
.matching-status {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.document-item,
.matching-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: var(--bg-subtle);
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
}

.doc-icon,
.organ-badge {
  font-size: 24px;
}

.doc-name,
.organ-value {
  font-weight: 700;
  color: var(--text);
}

.btn-action-view {
  margin-left: auto;
  border: 1px solid var(--border);
  background: var(--card-bg);
  color: var(--text);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  font-weight: 700;
  cursor: pointer;
}

.danger-zone {
  margin-top: 20px;
  padding: 14px;
  border: 2px solid var(--danger);
  border-radius: var(--radius);
  background: var(--danger-bg);
}

.danger-zone h4 {
  margin: 0 0 6px;
}

.danger-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-top: 10px;
}

.btn-danger {
  border: 1px solid var(--danger);
  background: var(--danger);
  color: #fff;
}

.btn-outline-danger {
  border: 1px solid var(--danger);
  background: transparent;
  color: var(--danger);
}

.doc-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  padding: 16px;
}

.doc-modal {
  width: min(900px, 100%);
  max-height: 90vh;
  background: var(--card-bg);
  border: 2px solid var(--border);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.doc-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 14px;
  border-bottom: 1px solid var(--border-soft);
}

.doc-modal-header h3 {
  margin: 0;
  font-size: 16px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.doc-modal-close {
  border: 1px solid var(--border);
  background: var(--bg-subtle);
  border-radius: var(--radius-sm);
  padding: 6px 10px;
  cursor: pointer;
}

.doc-modal-body {
  padding: 14px;
  overflow: auto;
}

.doc-preview-image {
  width: 100%;
  height: auto;
  border-radius: var(--radius-sm);
}

.doc-preview-frame {
  width: 100%;
  min-height: 70vh;
  border: 1px solid var(--border-soft);
  border-radius: var(--radius-sm);
  background: #fff;
}

@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: flex-start;
  }

  .progress-steps {
    flex-direction: column;
    align-items: stretch;
  }

  .progress-line {
    width: 2px;
    height: 28px;
    margin-left: 19px;
  }

  .status-grid,
  .profile-grid,
  .form-row {
    grid-template-columns: 1fr;
  }

  .form-actions {
    flex-direction: column;
  }

  .danger-actions {
    flex-direction: column;
  }

  .doc-preview-frame {
    min-height: 55vh;
  }
}
</style>
