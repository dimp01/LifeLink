<template>
  <div class="community">
    <header class="community-header">
      <div class="container">
        <h1>💬 Donor Community</h1>
        <p>Connect with fellow donors, share your journey, and inspire others to save lives.</p>
      </div>
    </header>

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

      <!-- Forum Tab - with backend integration -->
      <div v-if="activeTab === 'forum'" class="tab-content">
        <div class="forum-section">
          <!-- Create Post Form -->
          <div v-if="isLoggedIn" class="new-post-card">
            <h3>📝 Share Your Story</h3>
            <form @submit.prevent="submitPost">
              <div class="form-group">
                <input
                  v-model="newPost.title"
                  type="text"
                  placeholder="Post title..."
                  maxlength="100"
                  required
                />
              </div>
              <div class="form-group">
                <textarea
                  v-model="newPost.content"
                  placeholder="Share your thoughts... (minimum 10 characters)"
                  rows="4"
                  minlength="10"
                  required
                ></textarea>
              </div>
              <div class="form-group">
                <select v-model="newPost.post_type">
                  <option value="story">Success Story</option>
                  <option value="question">Question</option>
                  <option value="discussion">Discussion</option>
                </select>
              </div>
              <button type="submit" class="btn btn-primary" :disabled="postLoading">
                {{ postLoading ? "Publishing..." : "Publish Post" }}
              </button>
            </form>
            <div v-if="postMessage" class="alert alert-success">{{ postMessage }}</div>
            <div v-if="postError" class="alert alert-error">{{ postError }}</div>
          </div>

          <!-- Posts List -->
          <div class="posts-section">
            <div class="section-header">
              <h3>Community Posts</h3>
              <select v-model="postTypeFilter" class="filter-select">
                <option value="">All Posts</option>
                <option value="story">Success Stories</option>
                <option value="question">Questions</option>
                <option value="discussion">Discussions</option>
              </select>
            </div>

            <div v-if="postsLoading" class="loading">Loading posts...</div>
            <div v-else-if="filteredPosts.length === 0" class="empty-state">
              <div class="empty-icon">📭</div>
              <p>No posts yet</p>
            </div>
            <div v-else class="posts-list">
              <div v-for="post in filteredPosts" :key="post.id" class="post-card">
                <div class="post-header">
                  <div class="post-avatar">{{ post.author_name ? post.author_name[0].toUpperCase() : "A" }}</div>
                  <div>
                    <h4>{{ post.author_name || "Anonymous" }}</h4>
                    <p class="post-meta">{{ formatDate(post.created_at) }}</p>
                  </div>
                  <span v-if="post.post_type === 'story'" class="post-badge">✨ Story</span>
                  <span v-else-if="post.post_type === 'question'" class="post-badge">❓ Question</span>
                  <span v-else class="post-badge">💬 Discussion</span>
                </div>

                <h5 class="post-title">{{ post.title }}</h5>
                <p class="post-content">{{ post.content }}</p>

                <div class="post-actions">
                  <button
                    class="btn-action"
                    :class="{ liked: post.user_liked }"
                    @click="toggleLike(post.id, post.user_liked)"
                    :disabled="likingPost === post.id"
                  >
                    {{ post.user_liked ? "❤️" : "🤍" }} {{ post.like_count }}
                  </button>
                  <button class="btn-action" @click="sharePost(post)">📤 Share</button>
                  <button v-if="post.author_id === userId && isLoggedIn" class="btn-action" @click="deletePost(post.id)">
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Stats Tab -->
      <div v-if="activeTab === 'stats'" class="tab-content">
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">🫀</div>
            <div class="stat-content">
              <div class="stat-label">Total Donors</div>
              <div class="stat-value">15,420</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">♥️</div>
            <div class="stat-content">
              <div class="stat-label">Lives Saved</div>
              <div class="stat-value">46,260</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">👥</div>
            <div class="stat-content">
              <div class="stat-label">Active This Month</div>
              <div class="stat-value">3,240</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">⭐</div>
            <div class="stat-content">
              <div class="stat-label">Success Stories</div>
              <div class="stat-value">{{ posts.length }}</div>
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
const isLoggedIn = computed(() => auth.isLoggedIn)
const userId = computed(() => auth.userId)

const tabs = [
  { id: "forum", label: "💬 Forum" },
  { id: "stats", label: "📊 Statistics" },
]

const activeTab = ref("forum")
const posts = ref([])
const postsLoading = ref(false)
const postLoading = ref(false)
const postError = ref("")
const postMessage = ref("")
const likingPost = ref(null)
const postTypeFilter = ref("")

const newPost = ref({
  title: "",
  content: "",
  post_type: "story",
})

const filteredPosts = computed(() => {
  return posts.value.filter(
    p => postTypeFilter.value === "" || p.post_type === postTypeFilter.value
  )
})

function formatDate(dateString) {
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return "Just now"
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

async function loadPosts() {
  postsLoading.value = true
  try {
    const res = await api.get("/community/posts")
    posts.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    postsLoading.value = false
  }
}

async function submitPost() {
  if (!newPost.value.title.trim() || !newPost.value.content.trim()) return

  postLoading.value = true
  postError.value = ""
  postMessage.value = ""

  try {
    const res = await api.post("/community/posts", {
      title: newPost.value.title,
      content: newPost.value.content,
      post_type: newPost.value.post_type,
    })
    
    posts.value.unshift(res.data)
    newPost.value = { title: "", content: "", post_type: "story" }
    postMessage.value = "Post published successfully!"
    setTimeout(() => (postMessage.value = ""), 3000)
  } catch (e) {
    postError.value = e.response?.data?.detail || "Failed to publish post"
  } finally {
    postLoading.value = false
  }
}

async function toggleLike(postId, isLiked) {
  likingPost.value = postId
  try {
    if (isLiked) {
      await api.post(`/community/posts/${postId}/unlike`)
    } else {
      await api.post(`/community/posts/${postId}/like`)
    }
    await loadPosts()
  } catch (e) {
    console.error(e)
  } finally {
    likingPost.value = null
  }
}

async function deletePost(postId) {
  if (!confirm("Are you sure you want to delete this post?")) return

  try {
    await api.delete(`/community/posts/${postId}`)
    posts.value = posts.value.filter(p => p.id !== postId)
  } catch (e) {
    console.error(e)
  }
}

function sharePost(post) {
  const shareText = `${post.title}\n\n${post.content}`
  const shareUrl = window.location.href

  if (navigator.share) {
    navigator.share({
      title: "LifeLink - Community Post",
      text: shareText,
      url: shareUrl,
    })
  } else {
    navigator.clipboard.writeText(shareText)
    alert("Post copied to clipboard!")
  }
}

onMounted(loadPosts)
</script>

<style scoped>
.community {
  min-height: 100vh;
  background: #f8f9fa;
}

.community-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  text-align: center;
  padding: 60px 20px;
}

.community-header h1 {
  font-size: 2.5rem;
  font-weight: 900;
  margin-bottom: 10px;
}

.community-header p {
  opacity: 0.9;
  font-size: 1.1rem;
}

.community-content {
  padding: 40px 20px;
}

.community-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 30px;
  border-bottom: 2px solid #ddd;
}

.tab-btn {
  padding: 12px 20px;
  background: none;
  border: none;
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-muted);
  cursor: pointer;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-btn:hover {
  color: var(--text);
}

.tab-btn.active {
  color: var(--primary);
  border-bottom-color: var(--primary);
}

.tab-content {
  animation: fadeIn 0.3s;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.new-post-card {
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 30px;
  box-shadow: var(--shadow-sm);
}

.new-post-card h3 {
  margin: 0 0 20px 0;
  font-size: 1.3rem;
  font-weight: 800;
}

.form-group {
  margin-bottom: 14px;
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: 10px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
  font-family: inherit;
  resize: vertical;
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  gap: 12px;
}

.section-header h3 {
  margin: 0;
  font-size: 1.3rem;
  font-weight: 800;
}

.filter-select {
  padding: 8px 12px;
  border: 2px solid #ddd;
  border-radius: 6px;
  font-size: 0.95rem;
}

.posts-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.post-card {
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 20px;
  box-shadow: var(--shadow-sm);
  transition: transform 0.2s;
}

.post-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow);
}

.post-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.post-avatar {
  width: 40px;
  height: 40px;
  border: 2px solid #000;
  border-radius: 50%;
  background: var(--primary-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  flex-shrink: 0;
}

.post-header h4 {
  margin: 0 0 2px 0;
  font-size: 0.95rem;
  font-weight: 700;
}

.post-meta {
  margin: 0;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.post-badge {
  margin-left: auto;
  font-size: 0.75rem;
  background: var(--primary-light);
  color: var(--primary-dark);
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
}

.post-title {
  margin: 12px 0 8px 0;
  font-size: 1.1rem;
  font-weight: 700;
}

.post-content {
  margin: 0 0 12px 0;
  color: var(--text-soft);
  line-height: 1.6;
  font-size: 0.95rem;
}

.post-actions {
  display: flex;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #eee;
}

.btn-action {
  background: none;
  border: none;
  color: var(--text-muted);
  font-size: 0.95rem;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 4px;
  transition: all 0.2s;
  font-weight: 600;
}

.btn-action:hover {
  color: var(--primary);
  background: var(--primary-light);
}

.btn-action.liked {
  color: #e53e3e;
}

.alert {
  padding: 12px 16px;
  border-radius: 6px;
  margin-top: 12px;
  font-size: 0.9rem;
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

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 12px;
}

.loading {
  text-align: center;
  padding: 40px;
  color: var(--text-muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  background: white;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: var(--shadow-sm);
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-content {
  flex: 1;
}

.stat-label {
  color: var(--text-muted);
  font-size: 0.9rem;
  font-weight: 600;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 2rem;
  font-weight: 900;
  color: var(--primary);
}

@media (max-width: 768px) {
  .community-header h1 {
    font-size: 1.8rem;
  }

  .community-tabs {
    flex-wrap: wrap;
  }

  .section-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .filter-select {
    width: 100%;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stat-card {
    flex-direction: column;
    text-align: center;
  }
}
</style>
