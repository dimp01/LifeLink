import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  { path: '/', name: 'Home', component: () => import('../views/Home.vue'), meta: { title: 'LifeLink AI' } },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'), meta: { title: 'Login – LifeLink AI', isAuthPage: true } },
  { path: '/login-hospital', name: 'HospitalLogin', component: () => import('../views/HospitalLogin.vue'), meta: { title: 'Hospital Login – LifeLink AI', isAuthPage: true } },
  { path: '/admin-login', name: 'AdminLogin', component: () => import('../views/AdminLogin.vue'), meta: { title: 'Admin Login – LifeLink AI', isAuthPage: true } },
  { path: '/register', name: 'Register', component: () => import('../views/Register.vue'), meta: { title: 'Register – LifeLink AI', isAuthPage: true } },
  { path: '/about-donation', name: 'AboutDonation', component: () => import('../views/AboutDonation.vue'), meta: { title: 'About Donation – LifeLink AI' } },
  {
    path: '/donor',
    name: 'DonorDashboard',
    component: () => import('../views/DonorDashboard.vue'),
    meta: { requiresAuth: true, role: 'donor', title: 'Donor Dashboard – LifeLink AI' },
  },
  {
    path: '/recipient',
    name: 'RecipientDashboard',
    component: () => import('../views/RecipientDashboard.vue'),
    meta: { requiresAuth: true, role: 'recipient', title: 'Recipient Dashboard – LifeLink AI' },
  },
  {
    path: '/recipient/verify',
    name: 'RecipientVerification',
    component: () => import('../views/RecipientVerification.vue'),
    meta: { requiresAuth: true, role: 'recipient', title: 'Recipient Verification – LifeLink AI' },
  },
  {
    path: '/hospital',
    name: 'HospitalDashboard',
    component: () => import('../views/HospitalDashboard.vue'),
    meta: { requiresAuth: true, role: 'hospital', title: 'Hospital Dashboard – LifeLink AI' },
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: () => import('../views/AdminDashboard.vue'),
    meta: { requiresAuth: true, role: 'admin', title: 'Admin Dashboard – LifeLink AI' },
  },
  { path: '/awareness', name: 'Awareness', component: () => import('../views/Awareness.vue'), meta: { title: 'Awareness – LifeLink AI' } },
  { path: '/community', name: 'DonorCommunity', component: () => import('../views/DonorCommunity.vue'), meta: { title: 'Donor Community – LifeLink AI' } },
  { path: '/settings', name: 'UserSettings', component: () => import('../views/UserSettings.vue'), meta: { requiresAuth: true, title: 'Settings – LifeLink AI' } },
  { path: '/compliance', name: 'Compliance', component: () => import('../views/Compliance.vue'), meta: { requiresAuth: true, title: 'Legal & Compliance – LifeLink AI' } },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue'), meta: { title: 'Chat – LifeLink AI' } },
  {
    path: '/ml',
    name: 'MLDashboard',
    component: () => import('../views/MLDashboard.vue'),
    meta: { requiresAuth: true, title: 'ML Dashboard – LifeLink AI' },
  },
  // 404 catch-all route
  { path: '/:pathMatch(.*)*', name: 'NotFound', component: () => import('../views/NotFound.vue'), meta: { title: 'Page Not Found – LifeLink AI' } },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, savedPosition) {
    // Always scroll to top on route change
    return { top: 0 }
  }
})

router.beforeEach((to, from, next) => {
  const auth = useAuthStore()

  // If logged in and trying to access an auth page (login/register), redirect to dashboard
  if (auth.isLoggedIn && to.meta.isAuthPage) {
    return next(auth.dashboardRoute)
  }

  if (to.path === '/ml' && auth.isLoggedIn) {
    if (auth.role != 'admin') {
      return next(auth.dashboardRoute)
    }
  }

  // Redirect home to dashboard if logged in
  if (to.path === '/' && auth.isLoggedIn) {
    return next(auth.dashboardRoute)
  }

  // Requires authentication
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    if (to.path === '/admin') {
      return next('/admin-login')
    } else if (to.path === '/hospital') {
      return next('/login-hospital')
    }
    return next('/login')
  }

  // Enforce strict role matching on protected pages
  if (to.meta.requiresAuth && to.meta.role && auth.isLoggedIn && auth.role !== to.meta.role) {
    // If trying to access admin without admin rights, send to admin login
    if (to.path === '/admin') {
      return next('/admin-login')
    }
    // Otherwise, redirect to correct dashboard
    return next(auth.dashboardRoute)
  }

  // Role-based login access: users can visit OTHER role login pages
  if (to.meta.isAuthPage && auth.isLoggedIn) {
    const allowedLogins = {
      donor: ['/login-hospital', '/admin-login', '/admin'],
      recipient: ['/login-hospital', '/admin-login', '/admin'],
      hospital: ['/login', '/admin-login', '/admin'],
      admin: ['/login', '/login-hospital'],
    }

    const currentAllowed = allowedLogins[auth.role] || []
    if (!currentAllowed.includes(to.path)) {
      return next(auth.dashboardRoute)
    }
  }

  next()
})

router.afterEach((to) => {
  if (to.meta?.title) {
    document.title = to.meta.title
  }
})

export default router
