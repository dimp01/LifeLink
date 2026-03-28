<template>
  <div class="settings">
    <header class="settings-header">
      <div class="container">
        <h1>Settings & Preferences</h1>
        <p>Customize your LifeLink experience</p>
      </div>
    </header>

    <div class="container settings-content">
      <div class="settings-sidebar">
        <nav class="settings-nav">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            class="nav-item"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            <span class="nav-icon">{{ tab.icon }}</span>
            <span class="nav-label">{{ tab.label }}</span>
          </button>
        </nav>
      </div>

      <div class="settings-main">
        <!-- Appearance Tab -->
        <div v-if="activeTab === 'appearance'" class="settings-section">
          <h2>Appearance</h2>

          <div class="setting-group">
            <h3>Theme</h3>
            <p>Choose your preferred color scheme</p>
            <div class="theme-options">
              <button
                class="theme-option"
                :class="{ active: preferences.theme === 'light' }"
                @click="updateTheme('light')"
              >
                <div class="theme-preview light">
                  <div class="preview-header"></div>
                  <div class="preview-content"></div>
                </div>
                <span>Light</span>
              </button>
              <button
                class="theme-option"
                :class="{ active: preferences.theme === 'dark' }"
                @click="updateTheme('dark')"
              >
                <div class="theme-preview dark">
                  <div class="preview-header"></div>
                  <div class="preview-content"></div>
                </div>
                <span>Dark</span>
              </button>
            </div>
          </div>

          <div class="setting-group">
            <h3>Language</h3>
            <p>Select your preferred language</p>
            <select v-model="preferences.language" @change="updateLanguage">
              <option value="en">English</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="ta">தமிழ் (Tamil)</option>
              <option value="te">తెలుగు (Telugu)</option>
              <option value="bn">বাংলা (Bengali)</option>
            </select>
          </div>
        </div>

        <!-- Notifications Tab -->
        <div v-if="activeTab === 'notifications'" class="settings-section">
          <h2>Notifications</h2>

          <div class="setting-group">
            <h3>Email Notifications</h3>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.email"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>General Updates</strong>
                  <p>News, updates, and important announcements</p>
                </div>
              </label>
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.donationReminders"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>Donation Reminders</strong>
                  <p>Reminders for upcoming donation appointments</p>
                </div>
              </label>
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.communityUpdates"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>Community Updates</strong>
                  <p>Updates from support groups and community posts</p>
                </div>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <h3>Push Notifications</h3>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.push"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>Browser Notifications</strong>
                  <p>Receive notifications in your browser</p>
                </div>
              </label>
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.medicalAlerts"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>Medical Alerts</strong>
                  <p>Urgent medical updates and emergency notifications</p>
                </div>
              </label>
            </div>
          </div>

          <div class="setting-group">
            <h3>SMS Notifications</h3>
            <div class="checkbox-group">
              <label class="checkbox-item">
                <input
                  type="checkbox"
                  v-model="preferences.notifications.sms"
                  @change="updateNotifications"
                />
                <span class="checkmark"></span>
                <div>
                  <strong>Emergency SMS</strong>
                  <p>Critical alerts sent via SMS</p>
                </div>
              </label>
            </div>
          </div>
        </div>

        <!-- Privacy Tab -->
        <div v-if="activeTab === 'privacy'" class="settings-section">
          <h2>Privacy & Security</h2>

          <div class="setting-group">
            <h3>Profile Visibility</h3>
            <p>Control who can see your profile information</p>
            <select v-model="preferences.privacy.profileVisibility" @change="updatePrivacy">
              <option value="public">Public - Visible to everyone</option>
              <option value="community">Community - Visible to donors only</option>
              <option value="private">Private - Visible to you only</option>
            </select>
          </div>

          <div class="setting-group">
            <h3>Donation History</h3>
            <p>Show your donation history on your public profile</p>
            <label class="toggle">
              <input
                type="checkbox"
                v-model="preferences.privacy.showDonationHistory"
                @change="updatePrivacy"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="setting-group">
            <h3>Messages</h3>
            <p>Allow other users to send you messages</p>
            <label class="toggle">
              <input
                type="checkbox"
                v-model="preferences.privacy.allowMessages"
                @change="updatePrivacy"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>
        </div>

        <!-- Dashboard Tab -->
        <div v-if="activeTab === 'dashboard'" class="settings-section">
          <h2>Dashboard Customization</h2>

          <div class="setting-group">
            <h3>Layout</h3>
            <p>Choose your dashboard layout style</p>
            <div class="layout-options">
              <button
                class="layout-option"
                :class="{ active: preferences.dashboard.layout === 'grid' }"
                @click="updateDashboardLayout('grid')"
              >
                <div class="layout-preview grid">
                  <div class="grid-item"></div>
                  <div class="grid-item"></div>
                  <div class="grid-item"></div>
                  <div class="grid-item"></div>
                </div>
                <span>Grid</span>
              </button>
              <button
                class="layout-option"
                :class="{ active: preferences.dashboard.layout === 'list' }"
                @click="updateDashboardLayout('list')"
              >
                <div class="layout-preview list">
                  <div class="list-item"></div>
                  <div class="list-item"></div>
                  <div class="list-item"></div>
                </div>
                <span>List</span>
              </button>
            </div>
          </div>

          <div class="setting-group">
            <h3>Compact View</h3>
            <p>Use a more compact layout to fit more information</p>
            <label class="toggle">
              <input
                type="checkbox"
                v-model="preferences.dashboard.compactView"
                @change="updateDashboardSettings"
              />
              <span class="toggle-slider"></span>
            </label>
          </div>

          <div class="setting-group">
            <h3>Dashboard Widgets</h3>
            <p>Select which widgets to show on your dashboard</p>
            <div class="widgets-grid">
              <label
                v-for="widget in availableWidgets"
                :key="widget.id"
                class="widget-item"
                :class="{ active: preferences.dashboard.widgets.includes(widget.id) }"
              >
                <input
                  type="checkbox"
                  :value="widget.id"
                  v-model="preferences.dashboard.widgets"
                  @change="updateDashboardSettings"
                />
                <span class="widget-icon">{{ widget.icon }}</span>
                <span class="widget-name">{{ widget.name }}</span>
                <span class="widget-desc">{{ widget.description }}</span>
              </label>
            </div>
          </div>
        </div>

        <!-- Account Tab -->
        <div v-if="activeTab === 'account'" class="settings-section">
          <h2>Account Settings</h2>

          <div class="setting-group">
            <h3>Profile Information</h3>
            <div class="profile-info">
              <div class="info-item">
                <label>Name</label>
                <span>{{ user.full_name }}</span>
              </div>
              <div class="info-item">
                <label>Email</label>
                <span>{{ user.email }}</span>
              </div>
              <div class="info-item">
                <label>Role</label>
                <span>{{ user.role }}</span>
              </div>
              <div class="info-item">
                <label>User ID</label>
                <span>{{ user.user_id }}</span>
              </div>
            </div>
          </div>

          <div class="setting-group">
            <h3>Account Actions</h3>
            <div class="action-buttons">
              <button class="btn btn-outline" @click="exportData">
                Export My Data
              </button>
              <button class="btn btn-danger" @click="deleteAccount">
                Delete Account
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const user = computed(() => auth.user || {})
const preferences = computed(() => auth.userPreferences)

const activeTab = ref('appearance')

const tabs = [
  { id: 'appearance', label: 'Appearance', icon: '🎨' },
  { id: 'notifications', label: 'Notifications', icon: '🔔' },
  { id: 'privacy', label: 'Privacy', icon: '🔒' },
  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
  { id: 'account', label: 'Account', icon: '👤' },
]

const availableWidgets = [
  { id: 'stats', name: 'Statistics', description: 'Donation stats and metrics', icon: '📈' },
  { id: 'recent-activity', name: 'Recent Activity', description: 'Latest donations and updates', icon: '🕒' },
  { id: 'upcoming-events', name: 'Events', description: 'Upcoming donation camps and events', icon: '📅' },
  { id: 'quick-actions', name: 'Quick Actions', description: 'Fast access to common tasks', icon: '⚡' },
  { id: 'community', name: 'Community', description: 'Latest community posts', icon: '👥' },
  { id: 'achievements', name: 'Achievements', description: 'Your badges and milestones', icon: '🏆' },
]

// Methods
function updateTheme(theme) {
  auth.updatePreferences({ theme })
}

function updateLanguage() {
  auth.updatePreferences({ language: preferences.value.language })
}

function updateNotifications() {
  auth.updateNotifications(preferences.value.notifications)
}

function updatePrivacy() {
  auth.updatePreferences({ privacy: preferences.value.privacy })
}

function updateDashboardLayout(layout) {
  auth.updateDashboardSettings({ layout })
}

function updateDashboardSettings() {
  auth.updateDashboardSettings(preferences.value.dashboard)
}

function exportData() {
  // In real app, this would call an API to export user data
  alert('Data export feature would be implemented here. You would receive your data via email.')
}

function deleteAccount() {
  if (confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
    // In real app, this would call an API to delete the account
    alert('Account deletion would require additional verification steps.')
  }
}

onMounted(() => {
  // Any initialization needed
})
</script>

<style scoped>
.settings {
  min-height: 100vh;
  background: var(--bg);
}

.settings-header {
  background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
  color: white;
  padding: 60px 0;
  text-align: center;
}

.settings-header h1 {
  font-size: 3rem;
  font-weight: 900;
  margin-bottom: 16px;
}

.settings-header p {
  font-size: 1.2rem;
  opacity: 0.9;
  max-width: 600px;
  margin: 0 auto;
}

.settings-content {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 40px;
  padding: 40px 0;
}

.settings-sidebar {
  position: sticky;
  top: 20px;
  height: fit-content;
}

.settings-nav {
  background: var(--card-bg);
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  overflow: hidden;
  box-shadow: var(--shadow);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 16px 20px;
  border: none;
  background: transparent;
  color: var(--text);
  text-align: left;
  cursor: pointer;
  transition: var(--transition);
  border-bottom: 1px solid var(--border-soft);
}

.nav-item:last-child {
  border-bottom: none;
}

.nav-item:hover {
  background: var(--bg-subtle);
}

.nav-item.active {
  background: var(--accent);
  color: #000;
}

.nav-icon {
  font-size: 1.2rem;
  width: 24px;
  text-align: center;
}

.settings-main {
  min-height: 600px;
}

.settings-section h2 {
  font-size: 2rem;
  font-weight: 900;
  margin-bottom: 32px;
  color: var(--text);
}

.setting-group {
  background: var(--card-bg);
  border: 2px solid #000;
  border-radius: var(--radius-lg);
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: var(--shadow-sm);
}

.setting-group h3 {
  font-size: 1.2rem;
  font-weight: 800;
  margin-bottom: 8px;
  color: var(--text);
}

.setting-group p {
  color: var(--text-muted);
  margin-bottom: 16px;
  font-size: 0.9rem;
}

.setting-group select {
  width: 100%;
  max-width: 300px;
}

/* Theme Options */
.theme-options {
  display: flex;
  gap: 16px;
}

.theme-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  cursor: pointer;
  transition: var(--transition);
}

.theme-option:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}

.theme-option.active {
  border-color: var(--primary);
  background: var(--primary-light);
}

.theme-preview {
  width: 80px;
  height: 60px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

.theme-preview.light {
  background: #fff;
}

.theme-preview.light .preview-header {
  background: var(--primary);
  height: 15px;
}

.theme-preview.light .preview-content {
  background: #f5f5f5;
  height: 45px;
}

.theme-preview.dark {
  background: #1a1a1a;
}

.theme-preview.dark .preview-header {
  background: var(--primary);
  height: 15px;
}

.theme-preview.dark .preview-content {
  background: #2a2a2a;
  height: 45px;
}

/* Checkboxes */
.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.checkbox-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  cursor: pointer;
  padding: 12px;
  border-radius: var(--radius);
  transition: var(--transition);
}

.checkbox-item:hover {
  background: var(--bg-subtle);
}

.checkbox-item input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  cursor: pointer;
}

.checkmark {
  width: 20px;
  height: 20px;
  border: 2px solid var(--border);
  border-radius: var(--radius-sm);
  position: relative;
  flex-shrink: 0;
  margin-top: 2px;
}

.checkbox-item input:checked ~ .checkmark {
  background: var(--primary);
  border-color: var(--primary);
}

.checkbox-item input:checked ~ .checkmark::after {
  content: '✓';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 12px;
  font-weight: bold;
}

.checkbox-item div {
  flex: 1;
}

.checkbox-item strong {
  display: block;
  color: var(--text);
  margin-bottom: 4px;
}

.checkbox-item p {
  color: var(--text-muted);
  font-size: 0.85rem;
  margin: 0;
}

/* Toggle */
.toggle {
  position: relative;
  display: inline-block;
  width: 50px;
  height: 24px;
  cursor: pointer;
}

.toggle input {
  opacity: 0;
  width: 0;
  height: 0;
}

.toggle-slider {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--border-soft);
  border-radius: 24px;
  transition: var(--transition);
}

.toggle-slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background: white;
  border-radius: 50%;
  transition: var(--transition);
}

.toggle input:checked + .toggle-slider {
  background: var(--primary);
}

.toggle input:checked + .toggle-slider:before {
  transform: translateX(26px);
}

/* Layout Options */
.layout-options {
  display: flex;
  gap: 16px;
}

.layout-option {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  cursor: pointer;
  transition: var(--transition);
}

.layout-option:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow);
}

.layout-option.active {
  border-color: var(--primary);
  background: var(--primary-light);
}

.layout-preview {
  width: 80px;
  height: 60px;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 4px;
}

.layout-preview.grid {
  flex-wrap: wrap;
}

.layout-preview.grid .grid-item {
  flex: 1;
  background: var(--primary-light);
  border-radius: 2px;
}

.layout-preview.list .list-item {
  height: 8px;
  background: var(--primary-light);
  border-radius: 2px;
  margin-bottom: 2px;
}

/* Widgets */
.widgets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.widget-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border: 2px solid var(--border);
  border-radius: var(--radius);
  background: var(--card-bg);
  cursor: pointer;
  transition: var(--transition);
}

.widget-item:hover {
  transform: translate(-2px, -2px);
  box-shadow: var(--shadow-sm);
}

.widget-item.active {
  border-color: var(--primary);
  background: var(--primary-light);
}

.widget-item input {
  position: absolute;
  opacity: 0;
}

.widget-icon {
  font-size: 1.5rem;
  width: 32px;
  text-align: center;
}

.widget-name {
  font-weight: 700;
  color: var(--text);
}

.widget-desc {
  color: var(--text-muted);
  font-size: 0.85rem;
  flex: 1;
}

/* Profile Info */
.profile-info {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 0.8rem;
  font-weight: 700;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.info-item span {
  font-weight: 600;
  color: var(--text);
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

/* Responsive */
@media (max-width: 1024px) {
  .settings-content {
    grid-template-columns: 240px 1fr;
    gap: 24px;
  }
}

@media (max-width: 768px) {
  .settings-main {
    width: 98vw;
  }

  .settings-content {
    grid-template-columns: 1fr;
    gap: 24px;
  }

  .settings-sidebar {
    position: static;
    width: 99vw;
  }

  .settings-nav {
    display: flex;
    overflow-x: auto;
    padding: 0;
  }

  .nav-item {
    flex-shrink: 1;
    min-width: 120px;
    border-bottom: none;
    border-right: 1px solid var(--border-soft);
  }

  .nav-item:last-child {
    border-right: none;
  }

  .theme-options,
  .layout-options {
    flex-direction: column;
    align-items: stretch;
  }

  .widgets-grid {
    grid-template-columns: 1fr;
  }

  .profile-info {
    grid-template-columns: 1fr;
  }

  .checkbox-group {
    gap: 12px;
  }

  .checkbox-item {
    padding: 8px;
  }
}

@media (max-width: 640px) {
  .settings-header h1 {
    font-size: 2rem;
  }

  .settings-section h2 {
    font-size: 1.5rem;
  }

  .setting-group {
    padding: 20px;
  }

  .widgets-grid {
    gap: 8px;
  }

  .widget-item {
    padding: 12px;
    gap: 8px;
  }
}
</style>