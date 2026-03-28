<template>
  <div class="not-found">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>Page Not Found</h2>
      <p>The page you're looking for doesn't exist or has been moved.</p>
      <div class="not-found-actions">
        <router-link to="/" class="btn btn-primary">Go Home</router-link>
        <router-link to="/login" class="btn btn-outline">Log In</router-link>
      </div>
      <div class="not-found-help">
        <h3>Need Help?</h3>
        <ul>
          <li><router-link to="/awareness">Learn about organ donation</router-link></li>
          <li><router-link to="/register">Register as a donor or recipient</router-link></li>
          <li><router-link to="/chat">Ask our AI assistant</router-link></li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
// 404 Not Found page
</script>

<style scoped>
.not-found {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  padding: 20px;
}

.not-found-content {
  text-align: center;
  max-width: 500px;
}

.not-found-content h1 {
  font-size: 120px;
  font-weight: 900;
  color: var(--primary);
  margin: 0;
  line-height: 1;
}

.not-found-content h2 {
  font-size: 28px;
  font-weight: 800;
  margin: 10px 0 20px;
  color: var(--text);
}

.not-found-content p {
  font-size: 16px;
  color: var(--text-muted);
  margin-bottom: 30px;
}

.not-found-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 40px;
  flex-wrap: wrap;
}

.not-found-help {
  background: #fff;
  border: 2px solid #000;
  border-radius: 8px;
  padding: 24px;
  box-shadow: var(--shadow);
}

.not-found-help h3 {
  margin-top: 0;
  margin-bottom: 16px;
  font-size: 18px;
  font-weight: 700;
}

.not-found-help ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.not-found-help li {
  margin-bottom: 8px;
}

.not-found-help a {
  color: var(--primary);
  text-decoration: none;
  font-weight: 600;
}

.not-found-help a:hover {
  text-decoration: underline;
}

@media (max-width: 768px) {
  .not-found-content h1 {
    font-size: 80px;
  }
  .not-found-content h2 {
    font-size: 24px;
  }
  .not-found-actions {
    flex-direction: column;
    align-items: center;
  }
}
</style>