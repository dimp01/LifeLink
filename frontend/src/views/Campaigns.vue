<template>
  <div class="campaigns-container">
    <header class="campaigns-header">
      <h1>🚀 Awareness Campaigns</h1>
      <p>Join campaigns, spread awareness, and make a difference in organ donation!</p>
    </header>

    <div class="campaigns-content">
      <!-- Admin Campaign Management -->
      <div v-if="isAdmin" class="admin-section">
        <div class="admin-card">
          <h2>Create New Campaign</h2>
          <form @submit.prevent="createCampaign" class="campaign-form">
            <div class="form-group">
              <label>Campaign Title *</label>
              <input v-model="newCampaign.title" type="text" placeholder="Enter campaign title" required />
            </div>
            <div class="form-group">
              <label>Description *</label>
              <textarea v-model="newCampaign.description" placeholder="Campaign description" rows="3" required></textarea>
            </div>
            <div class="form-group">
              <label>Icon</label>
              <input v-model="newCampaign.icon" type="text" placeholder="e.g., 🎯" max length="5" />
            </div>
            <div class="form-row">
              <div class="form-group">
                <label>Campaign Type</label>
                <select v-model="newCampaign.campaign_type">
                  <option value="challenge">Challenge</option>
                  <option value="drive">Drive</option>
                  <option value="event">Event</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div class="form-group">
                <label>Target Participants</label>
                <input v-model.number="newCampaign.target_participants" type="number" min="1" />
              </div>
            </div>
            <button type="submit" class="btn btn-primary" :disabled="campaignLoading">
              {{ campaignLoading ? "Creating..." : "Create Campaign" }}
            </button>
          </form>
          <div v-if="campaignMessage" class="alert alert-success">{{ campaignMessage }}</div>
          <div v-if="campaignError" class="alert alert-error">{{ campaignError }}</div>
        </div>
      </div>

      <!-- Campaigns List -->
      <div class="campaigns-section">
        <div class="section-header">
          <h2>Available Campaigns</h2>
          <div class="filter-controls">
            <input v-model="searchQuery" type="text" placeholder="Search campaigns..." class="search-input" />
            <select v-model="filterType" class="filter-select">
              <option value="">All Types</option>
              <option value="challenge">Challenge</option>
              <option value="drive">Drive</option>
              <option value="event">Event</option>
            </select>
          </div>
        </div>

        <div v-if="campaignsLoading" class="loading">Loading campaigns...</div>
        <div v-else-if="filteredCampaigns.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>No campaigns available yet</p>
        </div>
        <div v-else class="campaigns-grid">
          <div v-for="campaign in filteredCampaigns" :key="campaign.id" class="campaign-card">
            <div class="campaign-card-header">
              <div class="campaign-icon">{{ campaign.icon }}</div>
              <div class="campaign-info">
                <h3>{{ campaign.title }}</h3>
                <span class="campaign-type">{{ campaign.campaign_type }}</span>
              </div>
            </div>
            <p class="campaign-description">{{ campaign.description }}</p>

            <div class="campaign-stats">
              <div class="stat">
                <span class="stat-label">Participants</span>
                <span class="stat-value">{{ campaign.participant_count }} / {{ campaign.target_participants }}</span>
              </div>
              <div class="stat">
                <span class="stat-label">Progress</span>
                <div class="progress-bar">
                  <div class="progress-fill" :style="{ width: (campaign.participant_count / campaign.target_participants * 100) + '%' }"></div>
                </div>
              </div>
            </div>

            <div class="campaign-actions">
              <button
                v-if="!campaign.user_joined"
                class="btn btn-primary btn-sm"
                @click="joinCampaign(campaign.id)"
                :disabled="joiningCampaign === campaign.id"
              >
                {{ joiningCampaign === campaign.id ? "Joining..." : "Join Campaign" }}
              </button>
              <button v-else class="btn btn-success btn-sm" @click="leaveCampaign(campaign.id)" :disabled="joiningCampaign === campaign.id">
                {{ joiningCampaign === campaign.id ? "Leaving..." : "✓ Joined" }}
              </button>
              <button class="btn btn-ghost btn-sm" @click="shareCampaign(campaign)">📤 Share</button>

              <!-- Admin Edit/Delete buttons -->
              <template v-if="isAdmin">
                <button class="btn btn-outline btn-sm" @click="editCampaign(campaign)">✎ Edit</button>
                <button class="btn btn-danger btn-sm" @click="deleteCampaign(campaign.id)" :disabled="deletingCampaign === campaign.id">
                  {{ deletingCampaign === campaign.id ? "Deleting..." : "✕ Delete" }}
                </button>
              </template>
            </div>
          </div>
        </div>
      </div>

      <!-- Admin Campaign Management Section -->
      <div v-if="isAdmin && managedCampaigns.length > 0" class="admin-management-section">
        <h2>Manage Your Campaigns</h2>
        <div class="managed-campaigns-list">
          <div v-for="campaign in managedCampaigns" :key="campaign.id" class="managed-campaign-item">
            <div class="managed-campaign-info">
              <h4>{{ campaign.title }}</h4>
              <p>{{ campaign.participant_count }} participants</p>
            </div>
            <div class="managed-campaign-actions">
              <router-link :to="`/campaigns/${campaign.id}/participants`" class="link-btn">View Participants</router-link>
              <button class="btn btn-sm btn-outline" @click="editCampaign(campaign)">Edit</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue"
import api from "../services/api.js"
import { useAuthStore } from "../stores/auth.js"

const auth = useAuthStore()
const isAdmin = computed(() => auth.role === "admin")

const campaigns = ref([])
const campaignsLoading = ref(false)
const campaignLoading = ref(false)
const campaignError = ref("")
const campaignMessage = ref("")
const joiningCampaign = ref(null)
const deletingCampaign = ref(null)

const searchQuery = ref("")
const filterType = ref("")

const newCampaign = ref({
  title: "",
  description: "",
  icon: "🎯",
  campaign_type: "challenge",
  target_participants: 100,
})

const filteredCampaigns = computed(() => {
  return campaigns.value.filter(c => {
    const matchesSearch = c.title.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      c.description.toLowerCase().includes(searchQuery.value.toLowerCase())
    const matchesType = filterType.value === "" || c.campaign_type === filterType.value
    return matchesSearch && matchesType
  })
})

const managedCampaigns = computed(() => {
  return campaigns.value.filter(c => c.created_by === auth.userId)
})

async function loadCampaigns() {
  campaignsLoading.value = true
  try {
    const res = await api.get("/campaigns")
    campaigns.value = res.data
  } catch (e) {
    campaignError.value = "Failed to load campaigns"
    console.error(e)
  } finally {
    campaignsLoading.value = false
  }
}

async function createCampaign() {
  campaignLoading.value = true
  campaignError.value = ""
  campaignMessage.value = ""

  try {
    const res = await api.post("/campaigns", newCampaign.value)
    campaigns.value.unshift(res.data)
    campaignMessage.value = "Campaign created successfully!"
    newCampaign.value = {
      title: "",
      description: "",
      icon: "🎯",
      campaign_type: "challenge",
      target_participants: 100,
    }
    setTimeout(() => (campaignMessage.value = ""), 3000)
  } catch (e) {
    campaignError.value = e.response?.data?.detail || "Failed to create campaign"
  } finally {
    campaignLoading.value = false
  }
}

async function joinCampaign(campaignId) {
  joiningCampaign.value = campaignId
  try {
    await api.post(`/campaigns/${campaignId}/join`)
    await loadCampaigns()
  } catch (e) {
    console.error(e)
  } finally {
    joiningCampaign.value = null
  }
}

async function leaveCampaign(campaignId) {
  joiningCampaign.value = campaignId
  try {
    await api.post(`/campaigns/${campaignId}/leave`)
    await loadCampaigns()
  } catch (e) {
    console.error(e)
  } finally {
    joiningCampaign.value = null
  }
}

async function deleteCampaign(campaignId) {
  if (!confirm("Are you sure you want to delete this campaign?")) return

  deletingCampaign.value = campaignId
  try {
    await api.delete(`/campaigns/${campaignId}`)
    campaigns.value = campaigns.value.filter(c => c.id !== campaignId)
  } catch (e) {
    console.error(e)
  } finally {
    deletingCampaign.value = null
  }
}

function editCampaign(campaign) {
  alert("Edit functionality will open a modal. Campaign: " + campaign.title)
}

function shareCampaign(campaign) {
  const shareText = `Join the "${campaign.title}" campaign on LifeLink! ${campaign.description}`
  const shareUrl = `${window.location.origin}/campaigns`

  if (navigator.share) {
    navigator.share({
      title: campaign.title,
      text: campaign.description,
      url: shareUrl,
    })
  } else {
    navigator.clipboard.writeText(`${campaign.title}: ${campaign.description}\n${shareUrl}`)
    alert("Campaign link copied to clipboard!")
  }
}

onMounted(loadCampaigns)
</script>

<style scoped>
.campaigns-container {
  min-height: 100vh;
  background: #f8f9fa;
}

.campaigns-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  text-align: center;
  padding: 60px 20px;
}

.campaigns-header h1 {
  font-size: 2.5rem;
  margin-bottom: 10px;
  font-weight: 900;
}

.campaigns-header p {
  font-size: 1.1rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto;
}

.campaigns-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 15px 20px;
}

.admin-section {
  margin-bottom: 40px;
}

.admin-card {
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 30px;
  box-shadow: var(--shadow);
}

.admin-card h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 800;
}

.campaign-form {
  display: grid;
  gap: 16px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-group label {
  font-weight: 600;
  font-size: 0.95rem;
}

.form-group input,
.form-group textarea,
.form-group select {
  padding: 10px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
  font-family: inherit;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  gap: 20px;
}

.section-header h2 {
  font-size: 1.8rem;
  font-weight: 800;
  margin: 0;
}

.filter-controls {
  display: flex;
  gap: 12px;
  flex: 1;
  max-width: 400px;
}

.search-input,
.filter-select {
  padding: 10px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
  min-height: 38px;
}

.search-input {
  flex: 1;
}

.filter-select {
  min-width: 140px;
}

.campaigns-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 40px;
}

.campaign-card {
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s, box-shadow 0.2s;
}

.campaign-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow);
}

.campaign-card-header {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.campaign-icon {
  font-size: 2rem;
  line-height: 1;
}

.campaign-info h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
}

.campaign-type {
  display: inline-block;
  background: var(--primary-light);
  color: var(--primary-dark);
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 700;
  margin-top: 4px;
}

.campaign-description {
  color: var(--text-soft);
  font-size: 0.95rem;
  line-height: 1.5;
  margin-bottom: 16px;
}

.campaign-stats {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 16px;
}

.stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
  font-size: 0.9rem;
}

.stat:last-child {
  margin-bottom: 0;
}

.stat-label {
  font-weight: 600;
}

.stat-value {
  font-weight: 700;
}

.progress-bar {
  width: 100px;
  height: 6px;
  background: #ddd;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s;
}

.campaign-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.btn-sm {
  padding: 6px 12px;
  font-size: 0.85rem;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 16px;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-top: 12px;
}

.alert-success {
  background: #dcfce7;
  color: #166534;
  border: 1px solid #86efac;
}

.alert-error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #fca5a5;
}

.admin-management-section {
  margin-top: 40px;
  padding: 30px;
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
}

.admin-management-section h2 {
  margin-bottom: 20px;
  font-size: 1.5rem;
  font-weight: 800;
}

.managed-campaigns-list {
  display: grid;
  gap: 12px;
}

.managed-campaign-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid var(--primary);
}

.managed-campaign-info h4 {
  margin: 0 0 4px 0;
  font-size: 1rem;
  font-weight: 700;
}

.managed-campaign-info p {
  margin: 0;
  font-size: 0.9rem;
  color: var(--text-muted);
}

.managed-campaign-actions {
  display: flex;
  gap: 12px;
}

.link-btn {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
  padding: 6px 12px;
  border-radius: 4px;
  transition: background 0.2s;
}

.link-btn:hover {
  background: var(--primary-light);
}

@media (max-width: 768px) {
  .campaigns-header h1 {
    font-size: 1.8rem;
  }

  .section-header {
    flex-direction: column;
    align-items: stretch;
  }

  .filter-controls {
    max-width: none;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .campaigns-grid {
    grid-template-columns: 1fr;
  }

  .managed-campaign-item {
    flex-direction: column;
    align-items: flex-start;
  }

  .managed-campaign-actions {
    width: 100%;
    margin-top: 12px;
  }
}
</style>
