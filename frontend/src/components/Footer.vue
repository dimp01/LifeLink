<template>
  <footer class="footer">
    <div class="container">
      <div class="footer-top">
        <div class="footer-brand">
          <div class="footer-logo">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="white"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
          </div>
          <div>
            <div class="footer-brand-name">LifeLink AI</div>
            <div class="footer-brand-sub">Intelligent Organ Donation Platform</div>
          </div>
        </div>
        <div class="footer-nav">
          <router-link to="/awareness">Awareness</router-link>
          <router-link to="/community" class="nav-link">Community</router-link>
          <router-link to="/about-donation">About Donation</router-link>
          <template v-if="!auth.isLoggedIn">
            <router-link to="/login">Log in</router-link>
            <router-link to="/register">Register</router-link>
          </template>
          <template v-if="auth.isLoggedIn">
            <router-link v-if="auth.role === 'donor' || auth.role === 'recipient'" to="/compliance" class="nav-link">Compliance</router-link>
          </template>
        </div>
      </div>
      <div class="footer-bottom">
        <p>© 2026 LifeLink AI · Built for research and public good · India</p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { useAuthStore } from '../stores/auth.js'
const auth = useAuthStore()
</script>

<style scoped>
/* Footer */
.footer { background: #0f172a; color: #e2e8f0; padding: 48px 0 0; border-top: 3px solid #000; }
.footer-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 36px;
  border-bottom: 2px solid rgba(255,255,255,0.12);
}
.footer-brand { display: flex; align-items: center; gap: 14px; }
.footer-logo {
  width: 36px; height: 36px;
  border-radius: 4px;
  background: var(--primary);
  border: 2px solid rgba(255,255,255,0.4);
  display: flex; align-items: center; justify-content: center;
}
.footer-brand-name { font-size: 17px; font-weight: 800; color: #fff; }
.footer-brand-sub { font-size: 12px; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.06em; }
.footer-nav { display: flex; gap: 24px; }
.footer-nav a { color: rgba(255,255,255,0.7); text-decoration: none; font-size: 14px; font-weight: 600; border-bottom: 2px solid transparent; padding-bottom: 2px; transition: all 0.15s; }
.footer-nav a:hover { color: var(--accent); border-bottom-color: var(--accent); }
.footer-bottom { padding: 18px 0; }
.footer-bottom p { font-size: 13px; color: rgba(255,255,255,0.35); text-align: center; }

@media (max-width: 768px) {
  .footer-top { flex-direction: column; gap: 20px; text-align: center; }
  .footer-nav { justify-content: center; flex-wrap: wrap; }
}
</style>