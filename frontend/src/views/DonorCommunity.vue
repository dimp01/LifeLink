<template>
  <div class="community">
    <header class="community-header">
      <div class="container">
        <h1>Donor Community</h1>
        <p>Connect with fellow donors, share your journey, and inspire others to save lives.</p>
      </div>
    </header>

    <!-- Hero Stats -->
    <section class="community-stats">
      <div class="container">
        <div class="stats-grid">
          <div class="stat-item">
            <div class="stat-number">{{ totalDonors }}</div>
            <div class="stat-label">Lives Saved</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ activeDonors }}</div>
            <div class="stat-label">Active Donors</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ successStories }}</div>
            <div class="stat-label">Success Stories</div>
          </div>
          <div class="stat-item">
            <div class="stat-number">{{ communities }}</div>
            <div class="stat-label">Support Groups</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Main Content -->
    <div class="container community-content">
      <div class="community-tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          class="tab-btn"
          :class="{ active: activeTab === tab.id }"
          @click="activeTab = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Success Stories Tab -->
      <div v-if="activeTab === 'stories'" class="tab-content">
        <div class="stories-grid">
          <div v-for="story in successStoriesData" :key="story.id" class="story-card">
            <div class="story-header">
              <div class="story-avatar">{{ story.author[0].toUpperCase() }}</div>
              <div>
                <h3>{{ story.author }}</h3>
                <p class="story-meta">{{ story.location }} • {{ story.date }}</p>
              </div>
            </div>
            <h4>{{ story.title }}</h4>
            <p class="story-content">{{ story.content }}</p>
            <div class="story-actions">
              <button class="btn-ghost" @click="likeStory(story.id)">
                ❤️ {{ story.likes }}
              </button>
              <button class="btn-ghost" @click="shareStory(story)">Share</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Support Groups Tab -->
      <div v-if="activeTab === 'groups'" class="tab-content">
        <div class="groups-grid">
          <div v-for="group in supportGroups" :key="group.id" class="group-card">
            <div class="group-header">
              <h3>{{ group.name }}</h3>
              <span class="group-members">{{ group.members }} members</span>
            </div>
            <p>{{ group.description }}</p>
            <div class="group-tags">
              <span v-for="tag in group.tags" :key="tag" class="tag">{{ tag }}</span>
            </div>
            <button class="btn btn-primary" @click="joinGroup(group.id)">
              {{ group.joined ? 'Leave Group' : 'Join Group' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Forums Tab -->
      <div v-if="activeTab === 'forums'" class="tab-content">
        <div class="forum-section">
          <div class="new-post-card">
            <h3>Start a Discussion</h3>
            <form @submit.prevent="createPost">
              <div class="form-group">
                <input v-model="newPost.title" type="text" placeholder="Post title..." required>
              </div>
              <div class="form-group">
                <textarea v-model="newPost.content" placeholder="Share your thoughts..." rows="4" required></textarea>
              </div>
              <button type="submit" class="btn btn-primary" :disabled="!newPost.title || !newPost.content">
                Post Discussion
              </button>
            </form>
          </div>

          <div class="posts-list">
            <div v-for="post in forumPosts" :key="post.id" class="post-card">
              <div class="post-header">
                <div class="post-avatar">{{ post.author[0].toUpperCase() }}</div>
                <div>
                  <h4>{{ post.title }}</h4>
                  <p class="post-meta">{{ post.author }} • {{ post.date }} • {{ post.replies }} replies</p>
                </div>
              </div>
              <p class="post-content">{{ post.content }}</p>
              <div class="post-actions">
                <button class="btn-ghost" @click="likePost(post.id)">👍 {{ post.likes }}</button>
                <button class="btn-ghost" @click="replyToPost(post.id)">Reply</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recognition Tab -->
      <div v-if="activeTab === 'recognition'" class="tab-content">
        <div class="recognition-section">
          <div class="leaderboard">
            <h3>🏆 Top Donors This Month</h3>
            <div class="leaderboard-list">
              <div v-for="(donor, index) in topDonors" :key="donor.id" class="leaderboard-item">
                <div class="rank">#{{ index + 1 }}</div>
                <div class="donor-info">
                  <div class="donor-avatar">{{ donor.name[0].toUpperCase() }}</div>
                  <div>
                    <h4>{{ donor.name }}</h4>
                    <p>{{ donor.donations }} donations • {{ donor.lives }} lives saved</p>
                  </div>
                </div>
                <div class="donor-badge">{{ donor.badge }}</div>
              </div>
            </div>
          </div>

          <div class="achievements">
            <h3>🎖️ Your Achievements</h3>
            <div class="achievements-grid">
              <div v-for="achievement in userAchievements" :key="achievement.id" class="achievement-card">
                <div class="achievement-icon">{{ achievement.icon }}</div>
                <h4>{{ achievement.title }}</h4>
                <p>{{ achievement.description }}</p>
                <span class="achievement-date">{{ achievement.date }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// Community data
const totalDonors = ref(15420)
const activeDonors = ref(3240)
const successStories = ref(89)
const communities = ref(12)

const activeTab = ref('stories')

const tabs = [
  { id: 'stories', label: 'Success Stories' },
  { id: 'groups', label: 'Support Groups' },
  { id: 'forums', label: 'Discussions' },
  { id: 'recognition', label: 'Recognition' }
]

// Success Stories
const successStoriesData = ref([
  {
    id: 1,
    author: 'Rajesh Kumar',
    location: 'Mumbai, Maharashtra',
    date: '2 days ago',
    title: 'My First Donation Saved a Life!',
    content: 'I was nervous about donating blood for the first time, but the staff at the center made me feel so comfortable. Two weeks later, I got a message that my blood helped save a young mother during childbirth. The feeling is indescribable!',
    likes: 24
  },
  {
    id: 2,
    author: 'Priya Sharma',
    location: 'Delhi, NCR',
    date: '1 week ago',
    title: 'From Recipient to Donor',
    content: 'I received a kidney transplant 3 years ago and promised myself I would give back. Today I became a regular blood donor. Every donation reminds me of the gift I received.',
    likes: 45
  },
  {
    id: 3,
    author: 'Amit Patel',
    location: 'Ahmedabad, Gujarat',
    date: '3 days ago',
    title: 'Family Tradition Continues',
    content: 'My grandfather was a regular donor, and now my whole family donates. We have a group tradition where we donate together. It is our way of honoring our heritage while helping others.',
    likes: 18
  }
])

// Support Groups
const supportGroups = ref([
  {
    id: 1,
    name: 'First-Time Donors',
    members: 1247,
    description: 'A supportive community for those taking their first steps into blood donation. Share experiences, ask questions, and get encouragement.',
    tags: ['Beginners', 'Support', 'Questions'],
    joined: true
  },
  {
    id: 2,
    name: 'Regular Donors Club',
    members: 892,
    description: 'For dedicated donors who give regularly. Share tips, track donation milestones, and motivate each other.',
    tags: ['Regular', 'Tips', 'Milestones'],
    joined: false
  },
  {
    id: 3,
    name: 'Organ Donors United',
    members: 456,
    description: 'Connect with others who have chosen to be organ donors. Share stories and support each other through the process.',
    tags: ['Organ', 'Legacy', 'Stories'],
    joined: true
  }
])

// Forum Posts
const forumPosts = ref([
  {
    id: 1,
    title: 'Tips for staying hydrated before donation?',
    author: 'Sneha Gupta',
    date: '5 hours ago',
    content: 'I always feel dizzy after donating. Any tips on staying hydrated and feeling better?',
    likes: 12,
    replies: 8
  },
  {
    id: 2,
    title: 'Best time to donate during exam season?',
    author: 'Vikram Singh',
    date: '1 day ago',
    content: 'I am a student and want to donate regularly, but exams are coming up. When is the best time to schedule donations?',
    likes: 6,
    replies: 15
  }
])

// Top Donors
const topDonors = ref([
  { id: 1, name: 'Dr. Ramesh Jain', donations: 156, lives: 468, badge: '🏆 Legend' },
  { id: 2, name: 'Sunita Verma', donations: 89, lives: 267, badge: '🥈 Champion' },
  { id: 3, name: 'Karan Mehta', donations: 67, lives: 201, badge: '🥉 Hero' }
])

// User Achievements
const userAchievements = ref([
  {
    id: 1,
    icon: '🎯',
    title: 'First Donation',
    description: 'Completed your first blood donation',
    date: 'Jan 15, 2024'
  },
  {
    id: 2,
    icon: '🔥',
    title: 'Streak Master',
    description: 'Donated 5 times in 6 months',
    date: 'Mar 10, 2024'
  },
  {
    id: 3,
    icon: '❤️',
    title: 'Life Saver',
    description: 'Your donations have helped save 3 lives',
    date: 'Apr 22, 2024'
  }
])

// New post form
const newPost = ref({
  title: '',
  content: ''
})

// Methods
function likeStory(storyId) {
  const story = successStoriesData.value.find(s => s.id === storyId)
  if (story) story.likes++
}

function shareStory(story) {
  if (navigator.share) {
    navigator.share({
      title: story.title,
      text: story.content,
      url: window.location.href
    })
  } else {
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(`${story.title}\n\n${story.content}\n\nShared from LifeLink AI`)
    alert('Story copied to clipboard!')
  }
}

function joinGroup(groupId) {
  const group = supportGroups.value.find(g => g.id === groupId)
  if (group) group.joined = !group.joined
}

function createPost() {
  if (!newPost.value.title || !newPost.value.content) return

  const post = {
    id: Date.now(),
    title: newPost.value.title,
    content: newPost.value.content,
    author: 'You', // In real app, get from auth
    date: 'Just now',
    likes: 0,
    replies: 0
  }

  forumPosts.value.unshift(post)
  newPost.value = { title: '', content: '' }
}

function likePost(postId) {
  const post = forumPosts.value.find(p => p.id === postId)
  if (post) post.likes++
}

function replyToPost(postId) {
  // In real app, this would open a reply modal
  alert('Reply functionality would open here!')
}

onMounted(() => {
  // In real app, fetch data from API
})
</script>

<style scoped>
.community {
  min-height: 100vh;
}

.community-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  padding: 60px 0;
  text-align: center;
}

.community-header h1 {
  font-size: 3rem;
  font-weight: 900;
  margin-bottom: 16px;
}

.community-header p {
  font-size: 1.2rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto;
}

.community-stats {
  padding: 40px 0;
  background: var(--bg-subtle);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stat-item {
  text-align: center;
  padding: 24px;
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow);
}

.stat-number {
  font-size: 2.5rem;
  font-weight: 900;
  color: var(--primary);
  margin-bottom: 8px;
}

.stat-label {
  font-size: 0.9rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--text-muted);
}

.community-tabs {
  display: flex;
  gap: 0;
  margin-bottom: 32px;
  border: 2px solid #000;
  border-radius: var(--radius);
  overflow: hidden;
  width: fit-content;
  box-shadow: var(--shadow-sm);
}

.tab-btn {
  padding: 12px 24px;
  border: none;
  background: white;
  color: var(--text-muted);
  font-weight: 700;
  cursor: pointer;
  transition: var(--transition);
  border-right: 2px solid #000;
}

.tab-btn:last-child {
  border-right: none;
}

.tab-btn.active {
  background: var(--accent);
  color: #000;
}

.tab-btn:hover:not(.active) {
  background: var(--bg-subtle);
  color: var(--text);
}

.tab-content {
  margin-top: 24px;
  margin-bottom: 24px;
}

.stories-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.story-card {
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow);
  transition: transform var(--transition), box-shadow var(--transition);
}

.story-card:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-lg);
}

.story-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.story-avatar {
  width: 40px;
  height: 40px;
  border: 2px solid #000;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--primary-dark);
}

.story-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.story-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 0;
}

.story-card h4 {
  margin: 16px 0 12px 0;
  font-size: 1.2rem;
  font-weight: 800;
}

.story-content {
  color: var(--text-soft);
  line-height: 1.6;
  margin-bottom: 16px;
}

.story-actions {
  display: flex;
  gap: 12px;
}

.btn-ghost {
  background: transparent;
  border: 2px solid #000;
  color: var(--text);
  padding: 6px 12px;
  font-size: 0.85rem;
  cursor: pointer;
  transition: var(--transition);
}

.btn-ghost:hover {
  background: var(--bg-subtle);
}

.groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 24px;
}

.group-card {
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 24px;
  box-shadow: var(--shadow);
}

.group-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 12px;
}

.group-header h3 {
  margin: 0;
  font-size: 1.2rem;
  font-weight: 800;
}

.group-members {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
}

.group-card p {
  color: var(--text-soft);
  margin-bottom: 16px;
  line-height: 1.5;
}

.group-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag {
  background: var(--accent);
  color: #000;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.forum-section {
  max-width: 800px;
  margin: 0 auto;
}

.new-post-card {
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 32px;
  box-shadow: var(--shadow);
}

.new-post-card h3 {
  margin-bottom: 20px;
  font-size: 1.3rem;
  font-weight: 800;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}

.post-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.post-avatar {
  width: 32px;
  height: 32px;
  border: 2px solid #000;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--primary-dark);
  font-size: 0.8rem;
}

.post-header h4 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 800;
}

.post-meta {
  font-size: 0.8rem;
  color: var(--text-muted);
  margin: 4px 0 0 0;
}

.post-content {
  color: var(--text-soft);
  line-height: 1.6;
  margin-bottom: 16px;
}

.post-actions {
  display: flex;
  gap: 12px;
}

.recognition-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 40px;
}

.leaderboard h3 {
  margin-bottom: 24px;
  font-size: 1.5rem;
  font-weight: 900;
}

.leaderboard-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.leaderboard-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.rank {
  font-size: 1.2rem;
  font-weight: 900;
  color: var(--primary);
  min-width: 40px;
}

.donor-info {
  display: flex;
  align-items: center;
  gap: 12px;
  flex: 1;
}

.donor-avatar {
  width: 40px;
  height: 40px;
  border: 2px solid #000;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  color: var(--primary-dark);
}

.donor-info h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 700;
}

.donor-info p {
  margin: 4px 0 0 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}

.donor-badge {
  font-size: 1.2rem;
}

.achievements h3 {
  margin-bottom: 24px;
  font-size: 1.5rem;
  font-weight: 900;
}

.achievements-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
}

.achievement-card {
  background: white;
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 20px;
  text-align: center;
  box-shadow: var(--shadow-sm);
}

.achievement-icon {
  font-size: 2rem;
  margin-bottom: 12px;
}

.achievement-card h4 {
  margin: 0 0 8px 0;
  font-size: 1.1rem;
  font-weight: 800;
}

.achievement-card p {
  color: var(--text-soft);
  margin: 0 0 12px 0;
  font-size: 0.9rem;
}

.achievement-date {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 600;
}

/* Responsive Design */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .recognition-section {
    grid-template-columns: 1fr;
    gap: 32px;
  }
}

@media (max-width: 768px) {
  .community-header h1 {
    font-size: 2rem;
  }

  .community-header p {
    font-size: 1rem;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .community-tabs {
    flex-wrap: wrap;
  }

  .tab-btn {
    flex: 1;
    min-width: 120px;
  }

  .stories-grid,
  .groups-grid {
    grid-template-columns: 1fr;
  }

  .leaderboard-item {
    flex-direction: column;
    text-align: center;
    gap: 8px;
  }

  .donor-info {
    flex-direction: column;
    gap: 8px;
  }
}

@media (max-width: 640px) {
  .community-header {
    padding: 40px 0;
  }

  .stat-item {
    padding: 20px;
  }

  .stat-number {
    font-size: 2rem;
  }
}
</style>