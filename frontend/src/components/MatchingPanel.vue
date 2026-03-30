<template>
  <div class="matching-panel">
    <div class="card" style="margin-bottom: 24px;">
      <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span>Smart Matching</span>
        <span class="badge badge-info">Ranked recipients for selected donor</span>
      </div>

      <div v-if="errorMessage" class="alert alert-error">{{ errorMessage }}</div>

      <div class="form-row" style="margin-bottom: 12px;">
        <div class="form-group">
          <label>Select Donor</label>
          <select v-if="hasDonorOptions" v-model="selectedDonorId" class="filter-select">
            <option value="">Choose donor</option>
            <option v-for="donor in donors" :key="donor.id" :value="String(donor.id)">
              {{ donor.full_name || donor.name || `Donor ${donor.id}` }} (ID: {{ donor.id }})
            </option>
          </select>
          <input
            v-else
            v-model="selectedDonorId"
            type="text"
            placeholder="Enter donor ID"
          />
        </div>

        <div class="form-group match-actions">
          <label>Run Matching</label>
          <button class="btn btn-primary" :disabled="!selectedDonorId || loading" @click="runMatching">
            {{ loading ? 'Matching...' : 'Match Donor' }}
          </button>
        </div>
      </div>

      <div v-if="loading" class="inline-loading" role="status" aria-live="polite">
        <div class="spinner"></div>
        <span class="text-sm text-muted">Evaluating ranked matches...</span>
      </div>

      <div class="matching-summary" v-if="lastMatchedDonorId && !loading">
        <span class="text-sm text-muted">Last run for donor ID:</span>
        <span class="badge badge-neutral">{{ lastMatchedDonorId }}</span>
        <span class="text-sm text-muted">Results:</span>
        <span class="badge" :class="matches.length ? 'badge-success' : 'badge-warning'">{{ matches.length }}</span>
      </div>
    </div>

    <div class="card">
      <div class="card-header" style="display: flex; justify-content: space-between; align-items: center; gap: 12px; flex-wrap: wrap;">
        <span>Ranked Recipient Matches</span>
        <button class="btn btn-outline btn-sm" :disabled="!selectedDonorId || loading" @click="runMatching">Refresh</button>
      </div>

      <div v-if="hasTopMatch" class="top-match-card" role="status" aria-live="polite">
        <div class="top-match-header">
          <span class="badge badge-success">Top Match</span>
          <strong class="top-match-score">Score: {{ formatScore(topMatch.match_score) }}</strong>
        </div>
        <div class="top-match-body">
          <div><strong>{{ topMatch.recipient_name || 'Unknown Recipient' }}</strong></div>
          <div class="text-sm text-muted">Recipient ID: {{ topMatch.recipient_id }}</div>
          <div v-if="topMatch.factors.length" class="factor-wrap" style="margin-top: 8px;">
            <span class="badge badge-info" v-for="factor in topMatch.factors" :key="factor">{{ factor }}</span>
          </div>
        </div>
      </div>

      <div v-if="loading" class="spinner-wrap">
        <div class="loading-state">
          <div class="spinner"></div>
          <div class="text-sm text-muted">Scoring recipients for donor {{ selectedDonorId }}...</div>
        </div>
      </div>

      <div v-else-if="!hasRun" class="empty-state">
        <div class="empty-icon">🎯</div>
        <p>Select a donor and run matching to view ranked recipients.</p>
      </div>

      <div v-else-if="matches.length === 0" class="empty-state">
        <div class="empty-icon">🔎</div>
        <p>No compatible recipients were returned for this donor. Try another donor or refresh data.</p>
      </div>

      <div v-else class="table-wrapper">
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Recipient Name</th>
              <th>Recipient ID</th>
              <th>Match Score</th>
              <th>Key Explanation Factors</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(match, index) in matches" :key="`${match.recipient_id}-${index}`">
              <template v-if="index === 0">
                <td>
                  <span class="badge badge-success">#1</span>
                </td>
                <td>
                  <strong>{{ match.recipient_name || 'Unknown Recipient' }}</strong>
                </td>
                <td>{{ match.recipient_id }}</td>
                <td>
                  <strong>{{ formatScore(match.match_score) }}</strong>
                </td>
                <td>
                  <div class="factor-wrap" v-if="match.factors.length">
                    <span class="badge badge-info" v-for="factor in match.factors" :key="factor">{{ factor }}</span>
                  </div>
                  <span v-else class="text-muted text-sm">No explanation factors</span>
                </td>
              </template>
              <template v-else>
              <td>
                <span class="badge badge-neutral">{{ index + 1 }}</span>
              </td>
              <td>{{ match.recipient_name || 'Unknown Recipient' }}</td>
              <td>{{ match.recipient_id }}</td>
              <td>
                <strong>{{ formatScore(match.match_score) }}</strong>
              </td>
              <td>
                <div class="factor-wrap" v-if="match.factors.length">
                  <span class="badge badge-info" v-for="factor in match.factors" :key="factor">{{ factor }}</span>
                </div>
                <span v-else class="text-muted text-sm">No explanation factors</span>
              </td>
              </template>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import api from '../services/api.js'

const props = defineProps({
  donors: {
    type: Array,
    default: () => [],
  },
  initialDonorId: {
    type: [String, Number],
    default: '',
  },
  autoLoad: {
    type: Boolean,
    default: false,
  },
  maxFactors: {
    type: Number,
    default: 3,
  },
})

const emit = defineEmits(['loaded', 'error'])

const selectedDonorId = ref(props.initialDonorId ? String(props.initialDonorId) : '')
const loading = ref(false)
const errorMessage = ref('')
const lastMatchedDonorId = ref('')
const matches = ref([])
const hasRun = ref(false)

const hasDonorOptions = computed(() => Array.isArray(props.donors) && props.donors.length > 0)
const topMatch = computed(() => (matches.value.length ? matches.value[0] : null))
const hasTopMatch = computed(() => !!topMatch.value)

watch(
  () => props.initialDonorId,
  (newVal) => {
    selectedDonorId.value = newVal ? String(newVal) : ''
  }
)

watch(
  () => props.donors,
  (newDonors) => {
    if (!selectedDonorId.value && Array.isArray(newDonors) && newDonors.length) {
      selectedDonorId.value = String(newDonors[0].id)
    }
  },
  { immediate: true }
)

function formatScore(score) {
  const numeric = Number(score)
  if (Number.isNaN(numeric)) return 'N/A'
  return numeric.toFixed(3)
}

function normalizeFactors(row) {
  if (Array.isArray(row.key_factors)) return row.key_factors
  if (Array.isArray(row.explanation_factors)) return row.explanation_factors
  if (Array.isArray(row.factors)) return row.factors
  if (row.explanation && typeof row.explanation === 'object') {
    const comp = row.explanation.components || {}
    const derived = []

    if (typeof comp.urgency_score === 'number') {
      derived.push(`Urgency ${(comp.urgency_score * 100).toFixed(0)}%`)
    }
    if (typeof comp.organ_with_blood_score === 'number') {
      derived.push(`Organ Fit ${(comp.organ_with_blood_score * 100).toFixed(0)}%`)
    } else if (typeof comp.organ_score === 'number') {
      derived.push(`Organ Fit ${(comp.organ_score * 100).toFixed(0)}%`)
    }
    if (typeof comp.blood_compatibility_score === 'number') {
      derived.push(`Blood Match ${(comp.blood_compatibility_score * 100).toFixed(0)}%`)
    }
    if (typeof comp.survival_score === 'number') {
      derived.push(`Survival ${(comp.survival_score * 100).toFixed(0)}%`)
    }

    if (derived.length) return derived
  }
  if (Array.isArray(row.explanations)) {
    return row.explanations
      .map((item) => item?.reason || item?.factor || item?.label || item)
      .filter(Boolean)
  }
  return []
}

function normalizeMatchRows(data) {
  const list = Array.isArray(data?.matches)
    ? data.matches
    : Array.isArray(data?.results)
      ? data.results
      : Array.isArray(data?.ranked_recipients)
        ? data.ranked_recipients
      : Array.isArray(data)
        ? data
        : []

  return list.map((row) => ({
    recipient_id: row.recipient_id ?? row.id ?? 'N/A',
    recipient_name: row.recipient_name ?? row.full_name ?? row.name ?? row.recipient?.full_name ?? '',
    match_score: row.match_score ?? row.score ?? row.total_score ?? 0,
    factors: normalizeFactors(row).slice(0, props.maxFactors),
  }))
}

async function runMatching() {
  if (!selectedDonorId.value) return

  loading.value = true
  errorMessage.value = ''
  hasRun.value = true

  try {
    const response = await api.matchDonor(selectedDonorId.value)
    matches.value = normalizeMatchRows(response.data)
    lastMatchedDonorId.value = String(selectedDonorId.value)
    emit('loaded', {
      donorId: lastMatchedDonorId.value,
      count: matches.value.length,
      matches: matches.value,
    })
  } catch (error) {
    matches.value = []
    errorMessage.value = error.response?.data?.detail || 'Unable to run matching right now.'
    emit('error', error)
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  if (props.autoLoad && selectedDonorId.value) {
    await runMatching()
  }
})
</script>

<style scoped>
.matching-panel {
  width: 100%;
}

.table-wrapper {
  overflow-x: auto;
}

.no-data {
  text-align: center;
  color: var(--text-muted);
  padding: 36px;
  font-size: 14px;
  font-weight: 600;
}

.matching-summary {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 4px;
}

.inline-loading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.top-match-card {
  border: 2px solid #000;
  border-radius: 6px;
  background: #f0fdf4;
  box-shadow: var(--shadow-sm);
  padding: 14px;
  margin-bottom: 16px;
}

.top-match-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}

.top-match-score {
  font-size: 13px;
}

.top-match-body {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.empty-state {
  text-align: center;
  padding: 46px 18px;
}

.empty-state .empty-icon {
  font-size: 34px;
  margin-bottom: 10px;
}

.empty-state p {
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 600;
  line-height: 1.45;
}

.factor-wrap {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.match-actions {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

@media (max-width: 768px) {
  .match-actions .btn {
    width: 100%;
  }

  .top-match-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
