<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title">Legal & Compliance Center</h1>
      <p class="page-subtitle">Secure digital documentation and audit trails for organ donation records</p>

      <!-- Tab Navigation -->
      <div class="compliance-tabs">
        <button v-for="tab in tabs" :key="tab.id"
          @click="activeTab = tab.id"
          class="tab-btn" :class="{ active: activeTab === tab.id }">
          {{ tab.icon }} {{ tab.name }}
        </button>
      </div>

      <!-- Digital Consent Forms -->
      <section v-if="activeTab === 'consent'" class="compliance-section">
        <h2>📋 Digital Consent Management</h2>
        <p class="section-desc">Securely store and manage your organ donation consent documents.</p>

        <div class="forms-grid">
          <div v-for="form in consentForms" :key="form.id" class="form-card">
            <div class="form-status" :class="'status-' + form.status">{{ form.status.toUpperCase() }}</div>
            <h3>{{ form.title }}</h3>
            <p>{{ form.description }}</p>
            <div class="form-meta">
              <span class="meta-item">📅 {{ new Date(form.createdAt).toLocaleDateString() }}</span>
              <span class="meta-item">🔐 {{ form.signature }}</span>
            </div>
            <div class="form-actions">
              <button class="btn btn-primary btn-sm" @click="viewDocument(form)">View</button>
              <button class="btn btn-ghost btn-sm" @click="downloadDocument(form)">📥 Download</button>
              <button v-if="form.status === 'pending'" class="btn btn-success btn-sm" @click="signDocument(form)">✍️ Sign</button>
            </div>
          </div>
        </div>

        <!-- New Consent Form -->
        <div class="new-form-section">
          <h3>Create New Consent Form</h3>
          <div class="form-builder">
            <div class="form-field">
              <label>Form Type</label>
              <select v-model="newForm.type">
                <option value="donor">Donor Consent Form</option>
                <option value="recipient">Recipient Agreement</option>
                <option value="family">Family Authorization</option>
              </select>
            </div>
            <div class="form-field">
              <label>Form Title</label>
              <input v-model="newForm.title" type="text" placeholder="Enter form title">
            </div>
            <div class="form-field">
              <label>Description</label>
              <textarea v-model="newForm.description" placeholder="Enter form description"></textarea>
            </div>
            <button class="btn btn-primary" @click="createForm">Create Form</button>
          </div>
        </div>
      </section>

      <!-- Digital Signatures -->
      <section v-if="activeTab === 'signatures'" class="compliance-section">
        <h2>✍️ Digital Signatures</h2>
        <p class="section-desc">Manage your digital signature certificates and signing authority.</p>

        <div class="signature-info">
          <div class="info-card">
            <div class="info-icon">🔐</div>
            <h3>Signature Status</h3>
            <div class="signature-status" :class="'status-' + signatureStatus">
              {{ signatureStatus === 'active' ? '✅ Active & Valid' : '⚠️ ' + signatureStatus.charAt(0).toUpperCase() + signatureStatus.slice(1) }}
            </div>
            <p>Certificate ID: {{ certificateId }}</p>
          </div>

          <div class="info-card">
            <div class="info-icon">📅</div>
            <h3>Certificate Validity</h3>
            <div class="validity-info">
              <p><strong>Issued:</strong> {{ signatureIssued }}</p>
              <p><strong>Expires:</strong> {{ signatureExpires }}</p>
              <div class="validity-bar">
                <div class="validity-fill" :style="{ width: certificateValidity + '%' }"></div>
              </div>
              <p class="validity-text">{{ certificateValidity }}% valid</p>
            </div>
          </div>

          <div class="info-card">
            <div class="info-icon">📊</div>
            <h3>Signatures Used</h3>
            <div class="usage-info">
              <p><strong>Total Signatures:</strong> {{ totalSignatures }}</p>
              <p><strong>This Month:</strong> {{ signaturesThisMonth }}</p>
              <p><strong>Remaining:</strong> {{ signatureLimitRemaining }}</p>
            </div>
          </div>
        </div>

        <!-- Revoke or Renew -->
        <div class="signature-actions">
          <button class="btn btn-warning" @click="revokeSignature">🔄 Revoke Certificate</button>
          <button class="btn btn-primary" @click="renewSignature">🆕 Request New Certificate</button>
        </div>
      </section>

      <!-- Audit Trail -->
      <section v-if="activeTab === 'audit'" class="compliance-section">
        <h2>📊 Audit Trail & Activity Log</h2>
        <p class="section-desc">Complete record of all actions and document changes for compliance.</p>

        <!-- Filter Options -->
        <div class="filter-section">
          <input v-model="auditFilter" type="text" placeholder="Search activity log..." class="search-input">
          <select v-model="auditType" class="filter-select">
            <option value="">All Activities</option>
            <option value="document">Document Changes</option>
            <option value="signature">Signatures</option>
            <option value="access">Access Logs</option>
            <option value="download">Downloads</option>
          </select>
        </div>

        <!-- Audit Timeline -->
        <div class="audit-timeline">
          <div v-for="event in filteredAuditEvents" :key="event.id" class="timeline-item" :class="'event-' + event.type">
            <div class="timeline-marker">
              <div class="marker-icon">{{ event.icon }}</div>
            </div>
            <div class="timeline-content">
              <div class="event-header">
                <h4>{{ event.action }}</h4>
                <span class="event-time">{{ formatTime(event.timestamp) }}</span>
              </div>
              <p class="event-details">{{ event.details }}</p>
              <div class="event-meta">
                <span class="meta">IP: {{ event.ip }}</span>
                <span class="meta">Device: {{ event.device }}</span>
                <span v-if="event.signature" class="meta">📝 Signed: {{ event.signature }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Export Audit Log -->
        <div class="export-section">
          <button class="btn btn-primary" @click="exportAuditLog">📥 Export as PDF</button>
          <button class="btn btn-ghost" @click="exportAuditLogJSON">📄 Export as JSON</button>
        </div>
      </section>

      <!-- Legal Documents -->
      <section v-if="activeTab === 'legal'" class="compliance-section">
        <h2>⚖️ Legal Documents & Policies</h2>
        <p class="section-desc">Review and acknowledge important legal documents.</p>

        <div class="legal-documents">
          <div v-for="doc in legalDocuments" :key="doc.id" class="legal-doc">
            <div class="doc-header">
              <h3>{{ doc.title }}</h3>
              <span class="doc-date">Updated: {{ new Date(doc.updatedAt).toLocaleDateString() }}</span>
            </div>
            <p>{{ doc.summary }}</p>
            <div class="doc-acknowledgment" v-if="!doc.acknowledged">
              <input type="checkbox" :id="'ack-' + doc.id" v-model="doc.acknowledged" @change="acknowledgeDocument(doc)">
              <label :for="'ack-' + doc.id">I acknowledge and agree to this document</label>
            </div>
            <div v-else class="doc-acknowledged">
              ✅ Acknowledged on {{ new Date(doc.acknowledgedDate).toLocaleDateString() }}
            </div>
            <div class="doc-actions">
              <button class="btn btn-ghost btn-sm" @click="viewLegalDoc(doc)">View Full Document</button>
              <button class="btn btn-ghost btn-sm" @click="downloadLegalDoc(doc)">📥 Download</button>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const activeTab = ref('consent')

// Tabs
const tabs = [
  { id: 'consent', name: 'Consent Forms', icon: '📋' },
  { id: 'signatures', name: 'Digital Signatures', icon: '✍️' },
  { id: 'audit', name: 'Audit Trail', icon: '📊' },
  { id: 'legal', name: 'Legal Docs', icon: '⚖️' }
]

// Consent Forms Data
const consentForms = ref([
  {
    id: 1,
    title: 'Organ Donor Registration',
    description: 'Official organ and tissue donation consent form',
    status: 'signed',
    signature: 'Digital - SHA256',
    createdAt: new Date('2024-01-15').toISOString(),
    signedBy: 'User'
  },
  {
    id: 2,
    title: 'Recipient Medical History',
    description: 'Comprehensive medical history for transplant evaluation',
    status: 'signed',
    signature: 'Digital - SHA256',
    createdAt: new Date('2024-02-20').toISOString(),
    signedBy: 'User'
  },
  {
    id: 3,
    title: 'Family Authorization Form',
    description: 'Authorization for family to make donation decisions',
    status: 'pending',
    signature: 'Waiting for signature',
    createdAt: new Date('2024-03-10').toISOString(),
    signedBy: null
  }
])

// New Form Model
const newForm = ref({
  type: 'donor',
  title: '',
  description: ''
})

// Digital Signatures Data
const signatureStatus = ref('active')
const certificateId = ref('CERT-2024-001-LIFELINK-AI')
const signatureIssued = ref('January 15, 2024')
const signatureExpires = ref('January 15, 2025')
const certificateValidity = ref(92)
const totalSignatures = ref(12)
const signaturesThisMonth = ref(3)
const signatureLimitRemaining = ref(988)

// Audit Trail Data
const auditFilter = ref('')
const auditType = ref('')

const auditEvents = ref([
  {
    id: 1,
    type: 'document',
    icon: '📝',
    action: 'Donor Registration Form Signed',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    details: 'You signed the official organ donor registration form with digital signature',
    ip: '192.168.1.1',
    device: 'Chrome on MacOS',
    signature: 'Valid - SHA256'
  },
  {
    id: 2,
    type: 'access',
    icon: '👁️',
    action: 'Account Accessed',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    details: 'Your account was accessed from a new device',
    ip: '203.0.113.45',
    device: 'Safari on iPhone',
    signature: null
  },
  {
    id: 3,
    type: 'download',
    icon: '📥',
    action: 'Document Downloaded',
    timestamp: new Date(Date.now() - 86400000).toISOString(),
    details: 'Organ Donor Registration Form (PDF) downloaded',
    ip: '192.168.1.1',
    device: 'Chrome on MacOS',
    signature: null
  },
  {
    id: 4,
    type: 'signature',
    icon: '✍️',
    action: 'Medical History Form Signed',
    timestamp: new Date(Date.now() - 172800000).toISOString(),
    details: 'You signed the comprehensive medical history form',
    ip: '192.168.1.1',
    device: 'Chrome on MacOS',
    signature: 'Valid - SHA256'
  },
  {
    id: 5,
    type: 'document',
    icon: '📝',
    action: 'Preferences Updated',
    timestamp: new Date(Date.now() - 259200000).toISOString(),
    details: 'Donation preferences updated: Added tissue donation',
    ip: '192.168.1.1',
    device: 'Chrome on MacOS',
    signature: null
  }
])

const filteredAuditEvents = computed(() => {
  return auditEvents.value.filter(event => {
    const matchesFilter = !auditFilter.value || 
      event.action.toLowerCase().includes(auditFilter.value.toLowerCase()) ||
      event.details.toLowerCase().includes(auditFilter.value.toLowerCase())
    
    const matchesType = !auditType.value || event.type === auditType.value
    
    return matchesFilter && matchesType
  })
})

// Legal Documents Data
const legalDocuments = ref([
  {
    id: 1,
    title: 'Terms of Service',
    summary: 'The terms and conditions governing the use of LifeLink AI platform.',
    updatedAt: new Date('2024-01-01').toISOString(),
    acknowledged: true,
    acknowledgedDate: new Date('2024-01-15').toISOString()
  },
  {
    id: 2,
    title: 'Privacy Policy',
    summary: 'How we collect, use, and protect your personal health information.',
    updatedAt: new Date('2024-02-15').toISOString(),
    acknowledged: true,
    acknowledgedDate: new Date('2024-02-20').toISOString()
  },
  {
    id: 3,
    title: 'HIPAA Compliance Statement',
    summary: 'Our commitment to HIPAA compliance and data protection standards.',
    updatedAt: new Date('2024-03-01').toISOString(),
    acknowledged: false
  },
  {
    id: 4,
    title: 'Data Retention Policy',
    summary: 'How long we retain your data and how you can request deletion.',
    updatedAt: new Date('2024-03-10').toISOString(),
    acknowledged: false
  }
])

// Functions
function viewDocument(form) {
  alert(`Viewing: ${form.title}\n\nDocument ID: ${form.id}\nStatus: ${form.status}\nSigned: ${form.signedBy || 'Not signed'}`)
}

function downloadDocument(form) {
  alert(`Downloading: ${form.title}.pdf`)
}

function signDocument(form) {
  form.status = 'signed'
  form.signature = 'Digital - SHA256'
  form.signedBy = 'User'
  
  // Add audit event
  auditEvents.value.unshift({
    id: auditEvents.value.length + 1,
    type: 'signature',
    icon: '✍️',
    action: `${form.title} Signed`,
    timestamp: new Date().toISOString(),
    details: `You signed the ${form.title}`,
    ip: '192.168.1.1',
    device: 'Chrome on MacOS',
    signature: 'Valid - SHA256'
  })
  
  alert(`✅ Document signed successfully!\n\nSignature: Digital - SHA256`)
}

function createForm() {
  if (!newForm.value.title) {
    alert('Please enter a form title')
    return
  }
  
  const form = {
    id: consentForms.value.length + 1,
    title: newForm.value.title,
    description: newForm.value.description,
    status: 'pending',
    signature: 'Waiting for signature',
    createdAt: new Date().toISOString(),
    signedBy: null
  }
  
  consentForms.value.push(form)
  newForm.value = { type: 'donor', title: '', description: '' }
  
  alert(`✅ Form created: ${form.title}`)
}

function revokeSignature() {
  signatureStatus.value = 'revoked'
  alert('⚠️ Certificate revoked. You will need to request a new certificate to sign documents.')
}

function renewSignature() {
  signatureStatus.value = 'pending'
  alert('📧 A new certificate request has been submitted. You\'ll receive it within 2-3 business days.')
}

function formatTime(timestamp) {
  const date = new Date(timestamp)
  const now = new Date()
  const diff = now - date
  
  if (diff < 3600000) return 'Just now'
  if (diff < 86400000) return Math.floor(diff / 3600000) + ' hours ago'
  if (diff < 604800000) return Math.floor(diff / 86400000) + ' days ago'
  
  return date.toLocaleDateString()
}

function exportAuditLog() {
  alert('📥 Exporting audit log as PDF...\n\nThe file has been downloaded.')
}

function exportAuditLogJSON() {
  const dataStr = JSON.stringify(filteredAuditEvents.value, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  const link = document.createElement('a')
  link.href = url
  link.download = `audit-log-${new Date().getTime()}.json`
  link.click()
  alert('✅ Audit log exported as JSON')
}

function acknowledgeDocument(doc) {
  if (doc.acknowledged) {
    doc.acknowledgedDate = new Date().toISOString()
    alert(`✅ You have acknowledged: ${doc.title}`)
  }
}

function viewLegalDoc(doc) {
  alert(`Viewing: ${doc.title}\n\n${doc.summary}`)
}

function downloadLegalDoc(doc) {
  alert(`📥 Downloading: ${doc.title}.pdf`)
}
</script>

<style scoped>
.page-title { font-size: 32px; font-weight: 900; margin-bottom: 8px; text-align: center; }
.page-subtitle { font-size: 16px; color: var(--text-muted); text-align: center; margin-bottom: 40px; }

.compliance-tabs {
  display: flex; gap: 12px; margin-bottom: 40px; flex-wrap: wrap;
  justify-content: center;
}

.tab-btn {
  padding: 12px 24px; border: 2px solid #000; background: #fff;
  border-radius: 6px; font-weight: 700; cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
  font-family: var(--font); box-shadow: 2px 2px 0 #000;
}

.tab-btn.active {
  background: var(--primary); color: #fff; box-shadow: var(--shadow-red);
}

.tab-btn:hover:not(.active) {
  background: var(--accent); transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 #000;
}

.compliance-section { margin-bottom: 52px; }
.compliance-section h2 { font-size: 28px; font-weight: 900; margin-bottom: 8px; }
.section-desc { color: var(--text-muted); margin-bottom: 24px; }

/* Consent Forms */
.forms-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px; margin-bottom: 40px;
}

.form-card {
  background: #fff; border: 2px solid #000; border-radius: 8px;
  padding: 24px; box-shadow: var(--shadow-md);
  transition: transform var(--transition), box-shadow var(--transition);
}

.form-card:hover { transform: translate(-2px, -2px); box-shadow: var(--shadow-lg); }

.form-status {
  display: inline-block; padding: 4px 12px; border-radius: 4px;
  font-size: 10px; font-weight: 800; margin-bottom: 12px;
  text-transform: uppercase; letter-spacing: 0.1em;
}

.form-status.status-signed { background: #d4edda; color: #155724; }
.form-status.status-pending { background: #fff3cd; color: #856404; }
.form-status.status-rejected { background: #f8d7da; color: #721c24; }

.form-card h3 { font-size: 18px; font-weight: 800; margin-bottom: 8px; }
.form-card p { color: var(--text-muted); font-size: 14px; margin-bottom: 16px; }

.form-meta { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
.meta-item { font-size: 12px; color: var(--text-faint); font-weight: 600; }

.form-actions { display: flex; gap: 8px; }
.form-actions .btn { flex: 1; }

.new-form-section {
  background: linear-gradient(135deg, #f8f9fa 0%, #ffffff 100%);
  border: 2px solid #000; border-radius: 8px; padding: 28px;
}

.new-form-section h3 { font-size: 20px; font-weight: 800; margin-bottom: 20px; }

.form-builder { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }

.form-field { display: flex; flex-direction: column; }
.form-field label { font-weight: 700; margin-bottom: 6px; }
.form-field input, .form-field select, .form-field textarea {
  padding: 10px; border: 2px solid #000; border-radius: 4px;
  font-family: var(--font); font-size: 14px;
}

.form-field textarea { grid-column: 1 / -1; min-height: 80px; }
.new-form-section .btn { grid-column: 1 / -1; }

/* Digital Signatures */
.signature-info {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px; margin-bottom: 40px;
}

.info-card {
  background: #fff; border: 2px solid #000; border-radius: 8px;
  padding: 24px; text-align: center; box-shadow: var(--shadow-md);
}

.info-icon { font-size: 32px; margin-bottom: 12px; }
.info-card h3 { font-size: 18px; font-weight: 800; margin-bottom: 12px; }

.signature-status {
  font-size: 16px; font-weight: 700; padding: 12px;
  border-radius: 4px; margin-bottom: 8px;
}

.signature-status.status-active { background: #d4edda; color: #155724; }
.signature-status.status-revoked { background: #f8d7da; color: #721c24; }
.signature-status.status-pending { background: #fff3cd; color: #856404; }

.usage-info p { font-size: 14px; margin: 8px 0; }

.validity-bar {
  height: 8px; background: #e9ecef; border-radius: 4px;
  overflow: hidden; margin: 12px 0;
}

.validity-fill { height: 100%; background: var(--primary); }
.validity-text { font-size: 12px; color: var(--text-muted); }

.signature-actions { display: flex; gap: 12px; }

/* Audit Trail */
.filter-section { display: flex; gap: 12px; margin-bottom: 24px; }
.search-input {
  flex: 1; padding: 10px 14px; border: 2px solid #000;
  border-radius: 4px; font-family: var(--font);
}

.filter-select {
  padding: 10px; border: 2px solid #000; border-radius: 4px;
  font-family: var(--font); font-weight: 600;
}

.audit-timeline {
  position: relative; padding: 20px 0;
}

.timeline-item {
  display: flex; gap: 20px; margin-bottom: 24px;
  position: relative;
}

.timeline-marker {
  flex-shrink: 0; position: relative;
}

.marker-icon {
  width: 40px; height: 40px; background: #fff;
  border: 2px solid #000; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-size: 18px; box-shadow: var(--shadow-md);
}

.timeline-item.event-signature .marker-icon { background: #e3f2fd; border-color: #1976d2; }
.timeline-item.event-access .marker-icon { background: #fff3e0; border-color: #f57c00; }
.timeline-item.event-download .marker-icon { background: #f3e5f5; border-color: #7b1fa2; }
.timeline-item.event-document .marker-icon { background: #e8f5e9; border-color: #388e3c; }

.timeline-content {
  background: #fff; border: 2px solid #000; border-radius: 6px;
  padding: 16px; flex: 1; box-shadow: var(--shadow-md);
}

.event-header { display: flex; justify-content: space-between; align-items: start; }
.event-header h4 { font-size: 16px; font-weight: 800; margin: 0; }
.event-time { font-size: 12px; color: var(--text-faint); font-weight: 600; }

.event-details { font-size: 14px; color: var(--text-muted); margin: 8px 0; }

.event-meta { display: flex; gap: 12px; flex-wrap: wrap; }
.meta { font-size: 12px; color: var(--text-faint); }

.export-section { display: flex; gap: 12px; margin-top: 24px; }

/* Legal Documents */
.legal-documents { display: grid; grid-template-columns: 1fr; gap: 16px; }

.legal-doc {
  background: #fff; border: 2px solid #000; border-radius: 8px;
  padding: 24px; box-shadow: var(--shadow-md);
}

.doc-header { display: flex; justify-content: space-between; align-items: start; margin-bottom: 12px; }
.doc-header h3 { font-size: 18px; font-weight: 800; margin: 0; }
.doc-date { font-size: 12px; color: var(--text-faint); }

.legal-doc > p { color: var(--text-muted); margin-bottom: 16px; }

.doc-acknowledgment, .doc-acknowledged {
  padding: 12px; background: #f8f9fa; border-radius: 4px;
  margin-bottom: 12px; font-size: 14px;
}

.doc-acknowledgment { display: flex; align-items: center; gap: 8px; }
.doc-acknowledgment input { width: 18px; height: 18px; cursor: pointer; }
.doc-acknowledged { background: #d4edda; color: #155724; }

.doc-actions { display: flex; gap: 8px; }

/* Responsive */
@media (max-width: 768px) {
  .compliance-tabs { flex-direction: column; align-items: stretch; }
  .tab-btn { width: 100%; }
  .form-builder { grid-template-columns: 1fr; }
  .filter-section { flex-direction: column; }
  .event-header { flex-direction: column; }
}

@media (max-width: 480px) {
  .page-title { font-size: 24px; }
  .forms-grid { grid-template-columns: 1fr; }
  .signature-info { grid-template-columns: 1fr; }
  .signature-actions { flex-direction: column; align-items: stretch; }
  .export-section { flex-direction: column; }
}
</style>
