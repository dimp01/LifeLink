<template>
  <div class="page">
    <div class="container">
      <h1 class="page-title">Awareness & Education Hub</h1>
      <p class="page-subtitle">Learn the truth about organ donation, your rights, and how to make a difference.</p>

      <!-- Type Filter -->
      <div class="type-filter">
        <button v-for="t in types" :key="t.id" class="type-btn" :class="{ active: activeType === t.id }"
          @click="activeType = t.id">
          {{ t.icon }} {{ t.label }}
        </button>
      </div>

      <div v-if="loading" class="spinner"></div>

      <!-- Content grid -->
      <div v-else-if="filteredContent.length" class="content-grid">
        <div class="content-card" v-for="item in filteredContent" :key="item.id" :class="'type-' + item.type">
          <div class="content-type-badge">{{ typeLabel(item.type) }}</div>
          <h3>{{ item.title }}</h3>
          <p>{{ item.content }}</p>
          <div class="content-date">{{ new Date(item.created_at).toLocaleDateString() }}</div>
        </div>
      </div>

      <div v-else class="empty-state">
        <div class="empty-icon">📚</div>
        <h3>No content available yet</h3>
        <p>Check back later or ask an admin to add awareness content.</p>
      </div>

      <!-- Campaign Tools Section -->
      <section class="campaign-tools">
        <h2>🚀 Awareness Campaigns</h2>
        <p>Join viral challenges and spread the word about organ donation!</p>

        <!-- Active Challenges -->
        <div class="challenges-grid">
          <div class="challenge-card" v-for="challenge in activeChallenges" :key="challenge.id">
            <div class="challenge-header">
              <div class="challenge-icon">{{ challenge.icon }}</div>
              <div class="challenge-meta">
                <h4>{{ challenge.title }}</h4>
                <span class="challenge-participants">{{ challenge.participants }} joined</span>
              </div>
            </div>
            <p class="challenge-desc">{{ challenge.description }}</p>
            <div class="challenge-actions">
              <button class="btn btn-primary btn-sm" @click="joinChallenge(challenge.id)"
                :disabled="userJoinedChallenges.includes(challenge.id)">
                {{ userJoinedChallenges.includes(challenge.id) ? '✅ Joined' : 'Join Challenge' }}
              </button>
              <button class="btn btn-ghost btn-sm" @click="shareChallenge(challenge)">
                📤 Share
              </button>
            </div>
          </div>
        </div>

        <!-- Social Sharing Tools -->
        <div class="sharing-tools">
          <h3>📢 Share Awareness</h3>
          <div class="share-buttons">
            <button class="share-btn twitter" @click="shareOnTwitter">
              🐦 Twitter
            </button>
            <button class="share-btn facebook" @click="shareOnFacebook">
              📘 Facebook
            </button>
            <button class="share-btn whatsapp" @click="shareOnWhatsApp">
              💬 WhatsApp
            </button>
            <button class="share-btn linkedin" @click="shareOnLinkedIn">
              💼 LinkedIn
            </button>
            <button class="share-btn copy" @click="copyShareLink">
              🔗 Copy Link
            </button>
          </div>
          <div class="share-stats">
            <div class="stat">
              <span class="stat-number">{{ totalShares }}</span>
              <span class="stat-label">Total Shares</span>
            </div>
            <div class="stat">
              <span class="stat-number">{{ campaignReach }}</span>
              <span class="stat-label">Campaign Reach</span>
            </div>
            <div class="stat">
              <span class="stat-number">{{ viralMultiplier }}</span>
              <span class="stat-label">Viral Multiplier</span>
            </div>
          </div>
        </div>

        <!-- Campaign Progress -->
        <div class="campaign-progress">
          <h3>📊 Campaign Progress</h3>
          <div class="progress-bars">
            <div class="progress-item">
              <div class="progress-label">Monthly Awareness Goal</div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: monthlyProgress + '%' }"></div>
              </div>
              <div class="progress-text">{{ monthlyProgress }}% Complete</div>
            </div>
            <div class="progress-item">
              <div class="progress-label">Challenge Participation</div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: challengeProgress + '%' }"></div>
              </div>
              <div class="progress-text">{{ challengeProgress }}% Active</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Quick Facts -->
      <section class="quick-facts">
        <h2>Quick Facts</h2>
        <div class="grid-3" style="display: grid;">
          <div class="fact-card" v-for="fact in quickFacts" :key="fact.stat">
            <div class="fact-stat">{{ fact.stat }}</div>
            <div class="fact-label">{{ fact.label }}</div>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import api from '../services/api.js'

const loading = ref(true)
const content = ref([])
const activeType = ref('all')

// Campaign Tools Data
const userJoinedChallenges = ref(JSON.parse(localStorage.getItem('joinedChallenges') || '[]'))
const totalShares = ref(1247)
const campaignReach = ref(15420)
const viralMultiplier = ref(12.3)
const monthlyProgress = ref(68)
const challengeProgress = ref(45)

const activeChallenges = ref([
  {
    id: 'heart-hero',
    title: 'Heart Hero Challenge',
    description: 'Share your story of why organ donation matters. Tag 3 friends to join!',
    icon: '❤️',
    participants: 2341
  },
  {
    id: 'myth-buster',
    title: 'Myth Buster Campaign',
    description: 'Debunk common organ donation myths. Use #OrganDonationMyths',
    icon: '🔍',
    participants: 1892
  },
  {
    id: 'pledge-day',
    title: 'National Pledge Day',
    description: 'Take the pledge and encourage others to do the same. Share your commitment!',
    icon: '🤝',
    participants: 3456
  },
  {
    id: 'story-share',
    title: 'Life Stories Challenge',
    description: 'Share stories of lives saved through donation. Every share counts!',
    icon: '📖',
    participants: 987
  }
])

const types = [
  { id: 'all', label: 'All', icon: '📋' },
  { id: 'myth', label: 'Myths & Facts', icon: '🔍' },
  { id: 'faq', label: 'FAQs', icon: '❓' },
  { id: 'legal', label: 'Legal Info', icon: '⚖️' },
  { id: 'blog', label: 'Articles', icon: '📖' },
]

const filteredContent = computed(() => {
  if (activeType.value === 'all') return content.value
  return content.value.filter(c => c.type === activeType.value)
})

function typeLabel(t) {
  return { myth: '🔍 Myth vs Fact', faq: '❓ FAQ', legal: '⚖️ Legal', blog: '📖 Article' }[t] || t
}

const quickFacts = [
  { stat: '1', label: 'donor can save up to 8 lives' },
  { stat: '500K+', label: 'people awaiting transplants in India' },
  { stat: '0.65', label: 'donors per million population in India (vs 40+ in Spain)' },
  { stat: '90%', label: 'of families support donation when asked' },
  { stat: '3 lakh+', label: 'needed kidney transplants per year' },
  { stat: '1994', label: 'THOA enacted, recognizing brain death' },
]

async function loadContent() {
  loading.value = true
  try {
    const res = await api.get('/awareness')
    content.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

// Campaign Functions
function joinChallenge(challengeId) {
  if (!userJoinedChallenges.value.includes(challengeId)) {
    userJoinedChallenges.value.push(challengeId)
    localStorage.setItem('joinedChallenges', JSON.stringify(userJoinedChallenges.value))

    // Update participant count
    const challenge = activeChallenges.value.find(c => c.id === challengeId)
    if (challenge) {
      challenge.participants++
    }

    // Show success message
    alert(`🎉 You've joined the ${challenge.title}! Share it with friends to spread awareness.`)
  }
}

function shareChallenge(challenge) {
  const shareText = `Join the ${challenge.title} for organ donation awareness! ${challenge.description} #OrganDonation #LifeLinkAI`
  const shareUrl = `${window.location.origin}/awareness`

  if (navigator.share) {
    navigator.share({
      title: challenge.title,
      text: shareText,
      url: shareUrl
    })
  } else {
    copyToClipboard(`${shareText} ${shareUrl}`)
    alert('Challenge link copied to clipboard!')
  }

  totalShares.value++
}

function shareOnTwitter() {
  const text = "Did you know 1 organ donor can save up to 8 lives? Join the movement! #OrganDonation #LifeLinkAI"
  const url = window.location.origin + '/awareness'
  window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`, '_blank')
  totalShares.value++
}

function shareOnFacebook() {
  const url = window.location.origin + '/awareness'
  window.open(`https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`, '_blank')
  totalShares.value++
}

function shareOnWhatsApp() {
  const text = "Did you know 1 organ donor can save up to 8 lives? Join the organ donation awareness movement! " + window.location.origin + '/awareness'
  window.open(`https://wa.me/?text=${encodeURIComponent(text)}`, '_blank')
  totalShares.value++
}

function shareOnLinkedIn() {
  const url = window.location.origin + '/awareness'
  const title = "Organ Donation Awareness - LifeLink AI"
  const summary = "Learn about organ donation and join the movement to save lives."
  window.open(`https://www.linkedin.com/sharing/share-offer?url=${encodeURIComponent(url)}&title=${encodeURIComponent(title)}&summary=${encodeURIComponent(summary)}`, '_blank')
  totalShares.value++
}

function copyShareLink() {
  const url = window.location.origin + '/awareness'
  copyToClipboard(url)
  alert('Awareness page link copied to clipboard!')
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {
    // Fallback for older browsers
    const textArea = document.createElement('textarea')
    textArea.value = text
    document.body.appendChild(textArea)
    textArea.select()
    document.execCommand('copy')
    document.body.removeChild(textArea)
  })
}

onMounted(loadContent)
</script>

<style scoped>
.type-filter {
  display: flex;
  gap: 8px;
  margin-bottom: 36px;
  flex-wrap: wrap;
}

.type-btn {
  padding: 8px 18px;
  border: 2px solid #000;
  background: #fff;
  border-radius: 4px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
  font-family: var(--font);
  color: var(--text);
  box-shadow: 2px 2px 0 #000;
}

.type-btn.active {
  background: var(--primary);
  color: #fff;
  box-shadow: var(--shadow-red);
}

.type-btn:hover:not(.active) {
  background: var(--accent);
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 #000;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  margin-bottom: 52px;
}

.content-card {
  background: #fff;
  border-radius: 6px;
  padding: 26px;
  box-shadow: var(--shadow-md);
  border: 2px solid #000;
  border-top: 6px solid #000;
  transition: transform var(--transition), box-shadow var(--transition);
}

.content-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-lg);
}

.content-card.type-myth {
  border-top-color: var(--primary);
}

.content-card.type-faq {
  border-top-color: var(--accent-dark);
}

.content-card.type-legal {
  border-top-color: var(--secondary);
}

.content-card.type-blog {
  border-top-color: var(--warning);
}

.content-type-badge {
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.content-card h3 {
  font-size: 15px;
  font-weight: 800;
  margin-bottom: 10px;
  color: var(--text);
}

.content-card p {
  font-size: 14px;
  color: var(--text-muted);
  line-height: 1.65;
  font-weight: 500;
}

.content-date {
  font-size: 12px;
  color: var(--text-faint);
  margin-top: 14px;
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 80px 0;
}

.empty-icon {
  font-size: 60px;
  margin-bottom: 16px;
}

.empty-state h3 {
  font-size: 20px;
  font-weight: 900;
  margin-bottom: 8px;
}

/* ── Campaign Tools ── */
.campaign-tools {
  margin-top: 52px;
  padding: 40px;
  padding-top: 52px;
  border-top: 3.4px solid #000;
  background: linear-gradient(135deg, #fef8e6 20%, #fffbf0 50%);
  border-radius: 14px;
  margin-bottom: 52px;
}

.campaign-tools h2 {
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -0.03em;
  margin-bottom: 8px;
  text-align: center;
  color: var(--text);
}

.campaign-tools>p {
  text-align: center;
  color: var(--text-muted);
  margin-bottom: 40px;
  font-size: 16px;
}

.challenges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.challenge-card {
  background: #fff;
  border: 3px solid #000;
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  transition: transform var(--transition), box-shadow var(--transition);
}

.challenge-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-lg);
}

.challenge-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.challenge-icon {
  font-size: 24px;
}

.challenge-meta h4 {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
  color: var(--text);
}

.challenge-participants {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
}

.challenge-desc {
  color: var(--text-muted);
  font-size: 14px;
  line-height: 1.5;
  margin-bottom: 16px;
  overflow-y: hidden;
  max-height: 60px;
  min-height: 60px;
}

.challenge-actions {
  display: grid;
  gap: 8px;
}

.challenge-actions .btn {
  flex: 1;
}

.sharing-tools {
  margin-bottom: 40px;
}

.sharing-tools h3 {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 20px;
  text-align: center;
  color: var(--text);
}

.share-buttons {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
  margin-bottom: 30px;
}

.share-btn {
  padding: 12px 20px;
  border: 2px solid #000;
  border-radius: 6px;
  background: #fff;
  font-weight: 700;
  cursor: pointer;
  transition: transform var(--transition), box-shadow var(--transition);
  box-shadow: 2px 2px 0 #000;
  font-size: 14px;
}

.share-btn:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 #000;
}

.share-btn.twitter:hover {
  background: #1da1f2;
  color: #fff;
  border-color: #1da1f2;
}

.share-btn.facebook:hover {
  background: #1877f2;
  color: #fff;
  border-color: #1877f2;
}

.share-btn.whatsapp:hover {
  background: #25d366;
  color: #fff;
  border-color: #25d366;
}

.share-btn.linkedin:hover {
  background: #0077b5;
  color: #fff;
  border-color: #0077b5;
}

.share-btn.copy:hover {
  background: var(--primary);
  color: #fff;
  border-color: var(--primary);
}

.share-stats {
  display: flex;
  justify-content: center;
  gap: 40px;
  flex-wrap: wrap;
}

.stat {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 32px;
  font-weight: 900;
  color: var(--primary);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.campaign-progress h3 {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 24px;
  text-align: center;
  color: var(--text);
}

.progress-bars {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.progress-item {
  margin-bottom: 16px;
}

.progress-label {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--text);
}

.progress-bar {
  height: 12px;
  background: #e9ecef;
  border-radius: 6px;
  border: 2px solid #000;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--primary);
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 600;
  margin-top: 4px;
  text-align: right;
}

.quick-facts {
  margin-top: 52px;
  padding-top: 52px;
  border-top: 3px solid #000;
}

.quick-facts h2 {
  font-size: 28px;
  font-weight: 900;
  letter-spacing: -0.03em;
  margin-bottom: 30px;
  text-align: center;
}

.fact-card {
  background: #fff;
  border-radius: 6px;
  padding: 28px;
  text-align: center;
  border: 2px solid #000;
  box-shadow: var(--shadow-md);
  transition: transform var(--transition), box-shadow var(--transition);
}

.fact-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-lg);
}

.fact-stat {
  font-size: 36px;
  font-weight: 900;
  color: var(--primary);
  margin-bottom: 8px;
}

.fact-label {
  font-size: 13px;
  color: var(--text-muted);
  font-weight: 600;
}

.grid-3 {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

@media (max-width: 1024px) {
  .grid-3 {
    gap: 10px;
  }
}

/* ── Responsive Design ── */
@media (max-width: 768px) {
  .campaign-tools {
    padding: 24px 20px;
  }

  .challenges-grid {
    grid-template-columns: 1fr;
  }

  .challenge-desc {
    min-height: auto;
  }

  .share-buttons {
    gap: 8px;
    align-items: center;
  }

  .share-btn {
    width: 200px;
  }

  .share-stats {
    gap: 20px;
  }

  .stat-number {
    font-size: 24px;
  }

  .progress-bars {
    gap: 16px;
  }

  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
    gap: 5px;
  }
}

@media (max-width: 480px) {
  .campaign-tools h2 {
    font-size: 24px;
  }

  .challenge-actions {
    flex-direction: column;
    display: flex;
    gap: 10px;
  }

  .challenge-actions .btn {
    width: 100%;
  }

  .share-stats {
    gap: 13px;
  }

  .share-btn {
    width: 160px;
    padding: 10px 16px;
  }

  .grid-3 {
    grid-template-columns: repeat(2, 1fr);
    gap: 0px
  }
}
</style>
