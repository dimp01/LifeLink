<template>
  <nav class="navbar" :class="{ 'scrolled': scrolled }">
    <div class="container navbar-inner">
      <!-- Brand -->
      <router-link to="/" class="brand">
        <div class="brand-icon-wrap">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
        </div>
        <span class="brand-name">LifeLink <strong>AI</strong></span>
      </router-link>

      <!-- Desktop nav -->
      <div class="nav-links">
        <router-link v-if="!auth.isLoggedIn" to="/" class="nav-link">Home</router-link>
        <router-link to="/awareness" class="nav-link">Awareness</router-link>
        <router-link to="/community" class="nav-link">Community</router-link>
        <template v-if="!auth.isLoggedIn">
          <router-link to="/chat" class="nav-link">💬 Chat</router-link>
        </template>
        <template v-if="auth.isLoggedIn">
          <router-link v-if="auth.role === 'admin'" to="/ml" class="nav-link">AI Insights</router-link>
          <router-link v-if="auth.role === 'donor' || auth.role === 'recipient'" to="/compliance" class="nav-link">Legal</router-link>
          <router-link :to="auth.dashboardRoute" class="nav-link">Dashboard</router-link>
          <router-link to="/settings" class="nav-link">Settings</router-link>
          <router-link to="/chat" class="nav-link">💬 Chat</router-link>
          <div class="user-pill btn-sm">
            <span class="user-avatar">{{ auth.user.full_name?.[0] || auth.role?.[0]?.toUpperCase() || '?' }}</span>
            <span class="user-role"><router-link to="/profile" style="text-decoration: none; color: inherit;">{{ auth.user?.full_name || auth.role }}</router-link></span>
          </div>
          <button class="btn btn-ghost btn-sm" @click="handleLogout">Sign out</button>
        </template>
        <template v-else>
          <router-link to="/login" class="btn btn-ghost btn-sm">Log in</router-link>
          <router-link to="/register" class="btn btn-primary btn-sm">Get started</router-link>
        </template>
      </div>
      <div class="user-pill hamburger" style="width:inherit; padding: inherit; right: 4.6rem; position: absolute;" v-if="auth.isLoggedIn">
        <span class="user-avatar">{{ auth.user.full_name?.[0] || auth.role?.[0]?.toUpperCase() || '?' }}</span>
        <span class="user-role"><router-link to="/profile" style="text-decoration: none; color: inherit;">{{ auth.user?.full_name || auth.role }}</router-link></span>
      </div>

      <!-- Mobile hamburger -->
      <button class="hamburger" @click="menuOpen = !menuOpen" :aria-expanded="menuOpen">
        <span :class="['bar', { open: menuOpen }]"></span>
      </button>
    </div>

    <!-- Mobile drawer -->
    <Transition name="drawer">
      <div class="mobile-menu" v-if="menuOpen">
        <router-link v-if="!auth.isLoggedIn" to="/" class="mob-link" @click="menuOpen = false">🏠 Home</router-link>
        <router-link to="/awareness" class="mob-link" @click="menuOpen = false">Awareness</router-link>
        <router-link to="/community" class="mob-link" @click="menuOpen = false">Community</router-link>
        <template v-if="!auth.isLoggedIn">
          <router-link to="/chat" class="mob-link" @click="menuOpen = false">💬 Chat</router-link>
        </template>
        <template v-if="auth.isLoggedIn">
          <router-link :to="auth.dashboardRoute" class="mob-link" @click="menuOpen = false">Dashboard</router-link>
          <router-link v-if="auth.role === 'admin' || auth.role === 'hospital'" to="/ml" class="mob-link" @click="menuOpen = false">AI Insights</router-link>
          <router-link v-if="auth.role === 'donor' || auth.role === 'recipient'" to="/compliance" class="mob-link" @click="menuOpen = false">Legal</router-link>
          <router-link to="/settings" class="mob-link" @click="menuOpen = false">Settings</router-link>
          <router-link to="/chat" class="mob-link" @click="menuOpen = false">💬 Chat</router-link>
          <div class="mob-divider"></div>
          <button class="btn btn-outline btn-sm w-full" @click="handleLogout">Sign out</button>
        </template>
        <template v-else>
          <div class="mob-divider"></div>
          <router-link to="/login" class="btn btn-ghost btn-sm" @click="menuOpen = false">Log in</router-link>
          <router-link to="/register" class="btn btn-primary btn-sm" @click="menuOpen = false">Get started</router-link>
        </template>
      </div>
    </Transition>
  </nav>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const auth = useAuthStore()
const router = useRouter()
const menuOpen = ref(false)
const scrolled = ref(false)

function handleLogout() {
  menuOpen.value = false
  auth.logout()
  router.push('/login')
}

function onScroll() { scrolled.value = window.scrollY > 12 }
onMounted(() => window.addEventListener('scroll', onScroll, { passive: true }))
onUnmounted(() => window.removeEventListener('scroll', onScroll))
</script>

<style scoped>
/* ── NeoBrutalism Navbar ── */
.navbar {
  position: sticky;
  top: 0;
  z-index: 200;
  background: #ffffff;
  border-bottom: 3px solid #000;
  box-shadow: 0 3px 0 #000;
  transition: none;
}
.navbar.scrolled {
  background: #ffffff;
}

.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 62px;
  gap: 12px;
}

/* Brand */
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  flex-shrink: 0;
}
.brand-icon-wrap {
  width: 36px; height: 36px;
  border-radius: 4px;
  background: var(--primary);
  border: 2px solid #000;
  box-shadow: 2px 2px 0 #000;
  display: flex; align-items: center; justify-content: center;
  color: #fff;
}
.brand-name {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  letter-spacing: -0.02em;
}
.brand-name strong { color: var(--primary); font-weight: 900; }

/* Nav links */
.nav-links {
  display: flex;
  align-items: center;
  gap: 6px;
}
.nav-link {
  text-decoration: none;
  color: var(--text-muted);
  font-size: 14px;
  font-weight: 600;
  padding: 7px 13px;
  border-radius: 4px;
  border: 2px solid transparent;
  transition: var(--transition);
}
.nav-link:hover {
  color: var(--text);
  background: var(--accent);
  border-color: #000;
}
.nav-link.router-link-active {
  color: #000;
  background: var(--accent);
  border: 2px solid #000;
  font-weight: 800;
}

/* User pill */
.user-pill {
  display: inline-flex; align-items: center; gap: 6px;
  height: 34px;
  padding: 0 12px;
  background: #fff;
  border-radius: 4px;
  /* border: 2px solid #000; */
  margin-left: 2px;
}
.user-avatar {
  width: 24px; height: 24px;
  border-radius: 4px;
  background: var(--primary);
  border: 1.5px solid #000;
  color: #fff;
  font-size: 11px;
  font-weight: 800;
  display: flex; align-items: center; justify-content: center;
}
.user-role {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-soft);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

/* Hamburger */
.hamburger {
  display: none;
  width: 38px; height: 38px;
  background: #fff;
  border: 2px solid #000;
  box-shadow: 2px 2px 0 #000;
  border-radius: 4px;
  cursor: pointer;
  align-items: center;
  justify-content: center;
  padding: 0;
  flex-shrink: 0;
  transition: transform var(--transition), box-shadow var(--transition);
}
.hamburger:hover { transform: translate(-1px,-1px); box-shadow: 3px 3px 0 #000; }
.hamburger:active { transform: translate(1px,1px); box-shadow: 1px 1px 0 #000; }
.bar {
  display: block;
  width: 18px; height: 2.5px;
  background: #000;
  border-radius: 1px;
  position: relative;
  transition: var(--transition);
}
.bar::before, .bar::after {
  content: '';
  position: absolute;
  width: 18px; height: 2.5px;
  background: #000;
  border-radius: 1px;
  transition: var(--transition);
}
.bar::before { top: -6px; left: 0}
.bar::after  { top: 6px; left: 0}
.bar.open { background: transparent; }
.bar.open::before { transform: rotate(45deg); top: 0; }
.bar.open::after  { transform: rotate(-45deg); top: 0; }

/* Mobile menu */
.mobile-menu {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px 20px 20px;
  border-top: 2px solid #000;
  background: #fffbf0;
}
.mob-link {
  text-decoration: none;
  color: var(--text);
  font-size: 15px;
  font-weight: 700;
  padding: 10px 14px;
  border-radius: 4px;
  border: 2px solid transparent;
  transition: var(--transition);
}
.mob-link:hover { background: var(--accent); border-color: #000; }
.mob-link.router-link-active { background: var(--accent); border: 2px solid #000; }
.mob-divider { height: 2px; background: #000; margin: 8px 0; }

/* Drawer transition */
.drawer-enter-active, .drawer-leave-active { transition: all 0.2s ease; }
.drawer-enter-from, .drawer-leave-to { opacity: 0; transform: translateY(-8px); }

@media (max-width: 768px) {
  .nav-links { display: none; }
  .hamburger { display: flex; }
  .navbar-inner { height: 56px; gap: 8px; }
  .brand-icon-wrap { width: 32px; height: 32px; }
  .brand-name { font-size: 16px; }
  .mobile-menu { padding: 12px 16px 16px; gap: 4px; }
  .mob-link { padding: 8px 12px; font-size: 14px; }
  .mob-divider { margin: 6px 0; }
}

@media (max-width: 480px) {
  .navbar { border-bottom: 2px solid #000; box-shadow: 0 2px 0 #000; }
  .navbar-inner { height: 52px; gap: 6px; }
  .brand { gap: 8px; }
  .brand-icon-wrap { width: 28px; height: 28px; box-shadow: 1px 1px 0 #000; }
  .brand-name { font-size: 14px; }
  .hamburger { width: 34px; height: 34px; box-shadow: 1px 1px 0 #000; }
  .bar { width: 16px; height: 2px; }
  .bar::before, .bar::after { width: 16px; height: 2px; }
  .bar::before { top: -5px; }
  .bar::after { top: 5px; }
  .mobile-menu { padding: 10px 12px 14px; gap: 3px; }
  .mob-link { padding: 7px 10px; font-size: 13px; }
}

</style>
