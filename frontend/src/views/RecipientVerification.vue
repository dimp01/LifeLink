<template>
  <div class="verify">
    <header class="verify-header">
      <h1>Recipient Verification</h1>
      <p>Your details are required to complete the legal verification process.</p>
      <br>
    </header>

    <div class="wizard">
      <div class="wizard-steps">
        <div
          v-for="s in steps"
          :key="s.id"
          class="wizard-step"
          :class="{ active: currentStep === s.id, complete: currentStep > s.id }
          "
        >
          <div class="step-circle">{{ s.id }}</div>
          <div class="step-label">{{ s.label }}</div>
        </div>
      </div>

      <div class="wizard-body">
        <component :is="currentComponent" :modelValue="formState" :validation-errors="validationErrors" @update:modelValue="updateFormState" />

        <div class="wizard-actions">
          <button class="btn btn-outline" @click="prevStep" :disabled="currentStep === 1">Back</button>
          <button
            class="btn btn-primary"
            @click="nextStep"
            :disabled="submitting"
          >
            {{ currentStep === steps.length ? 'Submit verification' : 'Next' }}
          </button>
        </div>

        <div v-if="submissionMessage" class="alert alert-success">
          {{ submissionMessage }}
        </div>
      </div>
    </div>

    <div v-if="showSummary" class="summary">
      <div class="summary-header">
        <h2>Verification Summary</h2>
        <p>Print or save this summary for your records.</p>
      </div>
      <div class="summary-body">
        <section>
          <h3>Profile</h3>
          <dl>
            <dt>Full name</dt>
            <dd>{{ user.full_name }}</dd>
            <dt>Email</dt>
            <dd>{{ user.email }}</dd>
            <dt>User ID</dt>
            <dd>{{ user.user_id }}</dd>
          </dl>
        </section>

        <section>
          <h3>Verification status</h3>
          <p><strong>{{ verification.status }}</strong></p>
          <p>Estimated review time: {{ verification.eta }}</p>
        </section>

        <section>
          <h3>Submitted information</h3>
          <div class="summary-grid">
            <div>
              <h4>Personal details</h4>
              <p><strong>Phone:</strong> {{ formState.personal.phone }}</p>
              <p><strong>Address:</strong> {{ formState.personal.address }}</p>
              <p><strong>Date of birth:</strong> {{ formState.personal.dob }}</p>
            </div>

            <div>
              <h4>Medical history</h4>
              <p><strong>Condition:</strong> {{ formState.medical.condition }}</p>
              <p><strong>Transplant needed:</strong> {{ formState.medical.transplantType }}</p>
              <p><strong>Notes:</strong> {{ formState.medical.notes }}</p>
            </div>

            <div>
              <h4>Hospital reference</h4>
              <p><strong>Name:</strong> {{ formState.hospital.name }}</p>
              <p><strong>Contact:</strong> {{ formState.hospital.contact }}</p>
              <p><strong>City:</strong> {{ formState.hospital.city }}</p>
            </div>

            <div>
              <h4>Consent</h4>
              <p>{{ formState.consent.agreed ? 'Agreed' : 'Not agreed' }}</p>
              <p><strong>Date:</strong> {{ formState.consent.date }}</p>
            </div>
          </div>
        </section>

        <div class="summary-actions">
          <button class="btn btn-outline" @click="printSummary">Print summary</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, reactive, ref, h, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()

const user = computed(() => auth.user || {})

const storageKey = `recipientVerification_${user.value?.user_id}`

// Define helper functions FIRST before using them
function loadState() {
  try {
    const raw = localStorage.getItem(storageKey)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function saveState() {
  formState.step = currentStep.value
  localStorage.setItem(storageKey, JSON.stringify(formState))
}

// NOW call loadState() after it's defined
const savedState = loadState() || {
  step: 1,
  status: 'Not started',
  submittedAt: null,
  eta: null,
  personal: {
    phone: '',
    address: '',
    dob: '',
  },
  medical: {
    condition: '',
    transplantType: '',
    notes: '',
  },
  documents: {
    medicalReports: [],
    prescriptions: [],
    idProof: null,
    photo: null,
    signature: null,
  },
  hospital: {
    name: '',
    contact: '',
    city: '',
  },
  consent: {
    agreed: false,
    date: '',
  },
}

const formState = reactive(savedState)
const currentStep = ref(formState.step)
const submitting = ref(false)
const submissionMessage = ref('')
const showSummary = ref(false)
const validationErrors = ref([])

// Watch for form state changes
watch(() => formState.personal, (newVal) => {
  console.log('formState.personal changed:', newVal)
}, { deep: true })

// Watch for all form state changes and save automatically
watch(formState, (newState) => {
  console.log('Form state changed, saving to localStorage:', newState)
  saveState()
}, { deep: true })

const VerificationPersonal = {
  props: ['modelValue', 'validationErrors'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const updateField = (field, value) => {
      console.log(`Updating ${field}:`, value)
      const updated = { ...props.modelValue, personal: { ...props.modelValue.personal, [field]: value } }
      console.log('Emitting update with:', updated)
      emit('update:modelValue', updated)
    }
    return { updateField }
  },
  render() {
    return h('div', { class: 'step' }, [
      this.$props.validationErrors && this.$props.validationErrors.length > 0 && h('div', { class: 'alert alert-error' }, [
        h('ul', {}, this.$props.validationErrors.map((err) => h('li', { key: err }, err)))
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Phone'),
        h('input', {
          type: 'tel',
          placeholder: '+91 98765 43210',
          value: this.$props.modelValue.personal.phone,
          onInput: (e) => this.updateField('phone', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Address'),
        h('textarea', {
          placeholder: 'Your full address',
          rows: 3,
          value: this.$props.modelValue.personal.address,
          onInput: (e) => this.updateField('address', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Date of birth'),
        h('input', {
          type: 'date',
          value: this.$props.modelValue.personal.dob,
          onInput: (e) => this.updateField('dob', e.target.value),
        }),
      ]),
    ])
  }
}

const VerificationMedical = {
  props: ['modelValue', 'validationErrors'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const updateField = (field, value) => {
      console.log(`Updating medical ${field}:`, value)
      const updated = { ...props.modelValue, medical: { ...props.modelValue.medical, [field]: value } }
      console.log('Emitting update with:', updated)
      emit('update:modelValue', updated)
    }
    return { props, updateField }
  },
  render() {
    return h('div', { class: 'step' }, [
      this.props.validationErrors.length > 0 && h('div', { class: 'alert alert-error' }, [
        h('ul', {}, this.props.validationErrors.map((err) => h('li', { key: err }, err)))
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Medical condition(s)'),
        h('input', {
          type: 'text',
          placeholder: 'E.g. Chronic kidney disease',
          value: this.props.modelValue.medical.condition,
          onInput: (e) => this.updateField('condition', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Transplant required'),
        h('input', {
          type: 'text',
          placeholder: 'E.g. Kidney',
          value: this.props.modelValue.medical.transplantType,
          onInput: (e) => this.updateField('transplantType', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Additional notes'),
        h('textarea', {
          placeholder: 'Any relevant medical history',
          rows: 3,
          value: this.props.modelValue.medical.notes,
          onInput: (e) => this.updateField('notes', e.target.value),
        }),
      ]),
    ])
  }
}

const VerificationDocuments = {
  props: ['modelValue', 'validationErrors'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const updateField = (field, value) => {
      console.log(`Updating documents ${field}:`, value)
      const updated = { ...props.modelValue, documents: { ...props.modelValue.documents, [field]: value } }
      console.log('Emitting update with:', updated)
      emit('update:modelValue', updated)
    }

    const handleFiles = (field, event) => {
      const files = Array.from(event.target.files)
      const valid = files.filter((file) => file.size <= 4 * 1024 * 1024)
      updateField(field, valid)
    }

    const handleSingleFile = (field, event) => {
      const file = event.target.files[0]
      if (!file) return
      if (file.size > 4 * 1024 * 1024) return
      updateField(field, file)
    }

    return { props, handleFiles, handleSingleFile }
  },
  render() {
    const renderFileList = (files) => {
      if (!files || files.length === 0) return null
      return h('div', { class: 'file-list' }, 
        files.map((file) => h('div', { class: 'file-item', key: file.name },
          `${file.name} (${(file.size / 1024 / 1024).toFixed(1)} MB)`
        ))
      )
    }

    return h('div', { class: 'step' }, [
      this.props.validationErrors.length > 0 && h('div', { class: 'alert alert-error' }, [
        h('ul', {}, this.props.validationErrors.map((err) => h('li', { key: err }, err)))
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Medical reports (PDF, JPG)'),
        h('input', {
          type: 'file',
          multiple: true,
          accept: '.pdf,image/*',
          onChange: (e) => this.handleFiles('medicalReports', e),
        }),
        renderFileList(this.props.modelValue.documents.medicalReports),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Prescriptions'),
        h('input', {
          type: 'file',
          multiple: true,
          accept: '.pdf,image/*',
          onChange: (e) => this.handleFiles('prescriptions', e),
        }),
        renderFileList(this.props.modelValue.documents.prescriptions),
      ]),
      h('div', { class: 'form-grid' }, [
        h('div', { class: 'form-group' }, [
          h('label', {}, 'ID proof'),
          h('input', {
            type: 'file',
            accept: '.pdf,image/*',
            onChange: (e) => this.handleSingleFile('idProof', e),
          }),
          this.props.modelValue.documents.idProof && h('div', { class: 'file-item' }, this.props.modelValue.documents.idProof.name),
        ]),
        h('div', { class: 'form-group' }, [
          h('label', {}, 'Photo'),
          h('input', {
            type: 'file',
            accept: 'image/*',
            onChange: (e) => this.handleSingleFile('photo', e),
          }),
          this.props.modelValue.documents.photo && h('div', { class: 'file-item' }, this.props.modelValue.documents.photo.name),
        ]),
        h('div', { class: 'form-group' }, [
          h('label', {}, 'Digital signature'),
          h('input', {
            type: 'file',
            accept: 'image/*',
            onChange: (e) => this.handleSingleFile('signature', e),
          }),
          this.props.modelValue.documents.signature && h('div', { class: 'file-item' }, this.props.modelValue.documents.signature.name),
        ]),
      ]),
    ])
  }
}

const VerificationHospital = {
  props: ['modelValue', 'validationErrors'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const updateField = (field, value) => {
      console.log(`Updating hospital ${field}:`, value)
      const updated = { ...props.modelValue, hospital: { ...props.modelValue.hospital, [field]: value } }
      console.log('Emitting update with:', updated)
      emit('update:modelValue', updated)
    }
    return { props, updateField }
  },
  render() {
    return h('div', { class: 'step' }, [
      this.props.validationErrors.length > 0 && h('div', { class: 'alert alert-error' }, [
        h('ul', {}, this.props.validationErrors.map((err) => h('li', { key: err }, err)))
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Hospital name'),
        h('input', {
          type: 'text',
          placeholder: 'Hospital / transplant centre',
          value: this.props.modelValue.hospital.name,
          onInput: (e) => this.updateField('name', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Contact'),
        h('input', {
          type: 'text',
          placeholder: 'Phone or email',
          value: this.props.modelValue.hospital.contact,
          onInput: (e) => this.updateField('contact', e.target.value),
        }),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'City'),
        h('input', {
          type: 'text',
          placeholder: 'City / region',
          value: this.props.modelValue.hospital.city,
          onInput: (e) => this.updateField('city', e.target.value),
        }),
      ]),
    ])
  }
}

const VerificationConsent = {
  props: ['modelValue', 'validationErrors'],
  emits: ['update:modelValue'],
  setup(props, { emit }) {
    const updateField = (field, value) => {
      console.log(`Updating consent ${field}:`, value)
      const updated = { ...props.modelValue, consent: { ...props.modelValue.consent, [field]: value } }
      console.log('Emitting update with:', updated)
      emit('update:modelValue', updated)
    }
    return { props, updateField }
  },
  render() {
    return h('div', { class: 'step' }, [
      this.props.validationErrors.length > 0 && h('div', { class: 'alert alert-error' }, [
        h('ul', {}, this.props.validationErrors.map((err) => h('li', { key: err }, err)))
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, [
          h('input', {
            type: 'checkbox',
            checked: this.props.modelValue.consent.agreed,
            onChange: (e) => this.updateField('agreed', e.target.checked),
          }),
          ' I declare that the information provided is true and accurate.',
        ]),
      ]),
      h('div', { class: 'form-group' }, [
        h('label', {}, 'Date'),
        h('input', {
          type: 'date',
          value: this.props.modelValue.consent.date,
          onInput: (e) => this.updateField('date', e.target.value),
        }),
      ]),
      h('div', { class: 'form-note' }, [
        h('p', {}, 'By submitting, you authorize LifeLink to use this information to facilitate medical verification and transplantation processes.'),
      ]),
    ])
  }
}

const steps = [
  { id: 1, label: 'Personal & contact details', component: VerificationPersonal },
  { id: 2, label: 'Medical history / transplant', component: VerificationMedical },
  { id: 3, label: 'Documents', component: VerificationDocuments },
  { id: 4, label: 'Hospital reference', component: VerificationHospital },
  { id: 5, label: 'Consent & submit', component: VerificationConsent },
]

const verification = computed(() => ({
  status: formState.status,
  eta: formState.eta,
  submittedAt: formState.submittedAt,
}))

const currentComponent = computed(() => {
  const step = steps.find((s) => s.id === currentStep.value)
  return step?.component || VerificationPersonal
})

function updateFormState(newState) {
  console.log('Updating formState with:', newState)
  Object.assign(formState, newState)
}

function validateStep() {
  validationErrors.value = []
  console.log(`=== Validating Step ${currentStep.value} ===`)
  
  if (currentStep.value === 1) {
    console.log('Personal data:', formState.personal)
    if (!formState.personal.phone) validationErrors.value.push('Phone is required')
    if (!formState.personal.address) validationErrors.value.push('Address is required')
    if (!formState.personal.dob) validationErrors.value.push('Date of birth is required')
  }
  if (currentStep.value === 2) {
    console.log('Medical data:', formState.medical)
    if (!formState.medical.condition) validationErrors.value.push('Medical condition is required')
    if (!formState.medical.transplantType) validationErrors.value.push('Transplant type is required')
  }
  if (currentStep.value === 3) {
    console.log('Documents data:', formState.documents)
    if (!formState.documents.medicalReports.length) validationErrors.value.push('At least one medical report is required')
    if (!formState.documents.prescriptions.length) validationErrors.value.push('At least one prescription is required')
    if (!formState.documents.idProof) validationErrors.value.push('ID proof is required')
    if (!formState.documents.photo) validationErrors.value.push('Photo is required')
    if (!formState.documents.signature) validationErrors.value.push('Signature is required')
  }
  if (currentStep.value === 4) {
    console.log('Hospital data:', formState.hospital)
    if (!formState.hospital.name) validationErrors.value.push('Hospital name is required')
    if (!formState.hospital.contact) validationErrors.value.push('Hospital contact is required')
    if (!formState.hospital.city) validationErrors.value.push('Hospital city is required')
  }
  if (currentStep.value === 5) {
    console.log('Consent data:', formState.consent)
    if (!formState.consent.agreed) validationErrors.value.push('You must agree to the declaration')
  }
  return validationErrors.value.length === 0
}

function nextStep() {
  console.log('Next step clicked. Current step:', currentStep.value)
  console.log('Current form state:', formState)
  if (!validateStep()) {
    console.log('Validation failed. Errors:', validationErrors.value)
    return
  }
  console.log('Validation passed')
  if (currentStep.value === steps.length) {
    submitVerification()
    return
  }
  currentStep.value += 1
  saveState()
}

function prevStep() {
  if (currentStep.value === 1) return
  currentStep.value -= 1
  saveState()
}

function submitVerification() {
  submitting.value = true
  setTimeout(() => {
    formState.status = 'Verification Under Process'
    formState.submittedAt = new Date().toISOString()
    formState.eta = '5-7 days'
    saveState()
    submissionMessage.value = 'Your verification has been submitted. You may print the summary below.'
    showSummary.value = true
    submitting.value = false
  }, 800)
}

function printSummary() {
  window.print()
}

// Clean up on unload
window.addEventListener('beforeunload', () => saveState())

</script>

<style scoped>
.verify {
  max-width: 980px;
  margin: 0 auto;
  padding: 40px 16px;
}

.verify-header h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.verify-header p {
  color: var(--text-muted);
  margin-top: 0;
}

.wizard {
  border: 2px solid #000;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: var(--shadow);
}

.wizard-steps {
  display: flex;
  background: var(--bg-subtle);
  border-bottom: 2px solid #000;
  overflow-x: auto;
}

.wizard-step {
  flex: 1;
  min-width: 120px;
  padding: 14px 10px;
  text-align: center;
  border-right: 1px solid rgba(0, 0, 0, 0.08);
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
}

.wizard-step:last-child {
  border-right: none;
}

.wizard-step.active {
  background: var(--primary);
  color: white;
}

.wizard-step.complete {
  background: rgba(76, 175, 80, 0.12);
}

.step-circle {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: rgba(0,0,0,0.06);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  margin-bottom: 6px;
}

.wizard-step.active .step-circle {
  background: rgba(255,255,255,0.2);
}

.step-label {
  font-size: 12px;
  font-weight: 600;
}

.wizard-body {
  padding: 28px;
  min-height: 300px;
  overflow-y: auto;
  max-height: 70vh;
}

.step {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

.form-note {
  background: var(--bg-subtle);
  padding: 14px 16px;
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-muted);
}

.file-list {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.file-item {
  background: var(--bg-subtle);
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 12px;
  color: var(--text);
  border-left: 3px solid var(--primary);
}

.wizard-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 22px;
  flex-wrap: wrap;
}

.alert {
  padding: 12px 14px;
  margin-top: 14px;
  border-radius: 6px;
}

.alert-success {
  background: rgba(56, 161, 105, 0.15);
  border: 1px solid rgba(56, 161, 105, 0.45);
}

.summary {
  margin-top: 40px;
}

.summary-header h2 {
  margin: 0;
}

.summary-body {
  background: #fff;
  border: 2px solid #000;
  border-radius: 10px;
  padding: 24px;
  box-shadow: var(--shadow);
  margin-top: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18px;
  margin-top: 20px;
}

.summary-grid h4 {
  margin: 0 0 8px;
}

.summary-body dl {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 10px 18px;
  margin: 0;
}

.summary-body dt {
  font-weight: 700;
  color: var(--text-muted);
}

.summary-actions {
  margin-top: 22px;
  display: flex;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .verify {
    padding: 24px 12px;
  }

  .verify-header h1 {
    font-size: 24px;
  }

  .wizard-steps {
    flex-wrap: wrap;
    gap: 0;
  }

  .wizard-step {
    flex: 1;
    min-width: 100px;
    padding: 10px 8px;
    font-size: 12px;
  }

  .step-label {
    font-size: 10px;
    word-break: break-word;
  }

  .step-circle {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .wizard-body {
    padding: 16px;
    max-height: 60vh;
    min-height: 250px;
  }

  .form-group {
    margin-bottom: 16px;
  }

  .form-group label {
    font-size: 11px;
  }

  .form-group input,
  .form-group textarea,
  .form-group select {
    font-size: 13px;
    padding: 9px 11px;
  }

  .form-grid {
    grid-template-columns: 1fr;
  }

  .wizard-actions {
    gap: 8px;
  }

  .btn {
    padding: 9px 16px;
    font-size: 13px;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .summary-body {
    padding: 16px;
  }

  .summary-body dl {
    grid-template-columns: 100px 1fr;
  }
}

@media (max-width: 480px) {
  .verify {
    padding: 16px 10px;
  }

  .verify-header h1 {
    font-size: 20px;
  }

  .verify-header p {
    font-size: 13px;
  }

  .wizard {
    border-radius: 6px;
  }

  .wizard-step {
    flex: 1;
    min-width: 70px;
    padding: 8px 5px;
    border-right: none;
  }

  .wizard-step:not(:last-child) {
    border-bottom: 1px solid rgba(0, 0, 0, 0.08);
  }

  .step-label {
    font-size: 9px;
    display: none;
  }

  .step-circle {
    width: 22px;
    height: 22px;
    font-size: 11px;
  }

  .wizard-body {
    padding: 12px;
    max-height: 55vh;
    min-height: 200px;
  }

  .form-group {
    margin-bottom: 14px;
  }

  .form-group label {
    font-size: 10px;
  }

  .form-group input,
  .form-group textarea,
  .form-group select {
    font-size: 12px;
    padding: 8px 10px;
  }

  .form-group textarea {
    min-height: 70px;
  }

  .wizard-actions {
    flex-direction: column;
    gap: 8px;
  }

  .wizard-actions button {
    width: 100%;
  }

  .btn {
    padding: 8px 14px;
    font-size: 12px;
  }

  .alert {
    font-size: 12px;
    padding: 10px 12px;
  }

  .summary-body dl {
    grid-template-columns: 80px 1fr;
    gap: 8px 14px;
  }

  .summary-body dt,
  .summary-body dd {
    font-size: 12px;
  }

  .file-item {
    font-size: 11px;
  }
}

</style>