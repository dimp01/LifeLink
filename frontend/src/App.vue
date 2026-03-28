<template>
  <div id="app-root">
    <Navbar v-if="showNavbar" />
    <main class="main-content">
      <router-view />
    </main>
    <Footer v-if="showFooter" />
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import Navbar from './components/Navbar.vue'
import Footer from './components/Footer.vue'

const route = useRoute()
const showNavbar = computed(() => !['Login', 'Register', 'HospitalLogin', 'AdminLogin'].includes(route.name))
const showFooter = computed(() => !['Login', 'Register', 'HospitalLogin', 'AdminLogin', 'Chat', 'NotFound'].includes(route.name))
</script>

<style>
#app-root {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
}
</style>
