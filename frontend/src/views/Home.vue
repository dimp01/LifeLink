<template>
  <div class="home">
    <!-- Hero Section -->
    <section class="hero">
      <div class="hero-bg-blobs">
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
      </div>
      <div class="container hero-inner">
        <div class="hero-content">
          <div class="hero-badge">
            <span class="badge-dot"></span>
            AI-Powered · India's First Intelligent Organ Donation Platform
          </div>
          <h1 class="hero-title">
            Every second matters.<br>
            <span class="gradient-text">LifeLink AI</span> makes them count.
          </h1>
          <p class="hero-desc">
            Machine-learning powered organ donation decision support — connecting donors,
            hospitals and administrators with real-time demand forecasting and explainable AI.
          </p>
          <div class="hero-actions">
            <router-link to="/register" class="btn btn-primary btn-xl">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/></svg>
              Become a Donor
            </router-link>
            <router-link to="/login#recipient" class="btn btn-ghost btn-xl">
              Find an Organ →
            </router-link>
          </div>
        </div>

        <div class="hero-stats-grid">
          <div class="hero-stat-card" v-for="stat in stats" :key="stat.label">
            <div class="hero-stat-icon">{{ stat.icon }}</div>
            <div class="hero-stat-value">{{ stat.value }}</div>
            <div class="hero-stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- Features -->
    <section class="features-section">
      <div class="container">
        <div class="section-header">
          <div class="section-eyebrow">Platform Features</div>
          <h2 class="section-title">Everything you need in one platform</h2>
          <p class="section-sub">End-to-end organ donation management powered by AI</p>
        </div>
        <div class="features-grid">
          <div class="feature-card" v-for="f in features" :key="f.icon">
            <div class="feature-icon-wrap">{{ f.icon }}</div>
            <h3>{{ f.title }}</h3>
            <p>{{ f.desc }}</p>
            <div class="feature-tag">{{ f.tag }}</div>
          </div>
        </div>
      </div>
    </section>

    <!-- How It Works -->
    <section class="how-section">
      <div class="container">
        <div class="section-header">
          <div class="section-eyebrow">Process</div>
          <h2 class="section-title">How LifeLink AI works</h2>
        </div>
        <div class="steps-row">
          <div class="step-item" v-for="(step, i) in steps" :key="i">
            <div class="step-connector" v-if="i > 0"></div>
            <div class="step-bubble">
              <span>{{ step.icon }}</span>
            </div>
            <div class="step-info">
              <span class="step-num">Step {{ i + 1 }}</span>
              <h3>{{ step.title }}</h3>
              <p>{{ step.desc }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Insight Strip -->
    <section class="insight-strip">
      <div class="container insight-inner">
        <div class="insight-icon">🤖</div>
        <div>
          <h3>Trained on real survey data from 20 Indian cities</h3>
          <p>Our XGBoost model achieved 63.6% accuracy on 55 real responses — top predictor: family support for donation.</p>
        </div>
        <router-link to="/awareness" class="btn btn-primary">View Insights →</router-link>
      </div>
    </section>

    <!-- CTA -->
    <section class="cta-section">
      <div class="cta-bg"></div>
      <div class="container cta-inner">
        <h2>One organ donor can save up to <span>8 lives</span></h2>
        <p>Join the movement. Register today and give someone the gift of life.</p>
        <div class="cta-actions">
          <router-link to="/register" class="btn btn-primary btn-xl">Start your registration</router-link>
          <router-link to="/about-donation" class="btn btn-secondary btn-xl">Learn more →</router-link>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
const stats = [
  { icon: '🩸', value: '5L+',  label: 'Registered donors' },
  { icon: '🏥', value: '500K', label: 'Awaiting transplant' },
  { icon: '🤖', value: '20',   label: 'Cities analysed by AI' },
  { icon: '⚡', value: '8',    label: 'Lives per donor' },
]
const features = [
  { icon: '🩸', title: 'Donor Registration', desc: 'Multi-step digital registration with organ preferences, consent management and status tracking.', tag: 'For Donors' },
  { icon: '🤖', title: 'AI Demand Forecasting', desc: 'XGBoost-powered organ demand predictions with 3–6 month regional projections.', tag: 'ML Powered' },
  { icon: '📊', title: 'ODII Index', desc: 'Organ Demand Instability Index — a novel research metric quantifying regional shortage risk.', tag: 'Research' },
  { icon: '🔍', title: 'Explainable AI', desc: 'SHAP-based transparency: understand exactly why each prediction is made.', tag: 'XAI' },
  { icon: '🏥', title: 'Hospital Dashboard', desc: 'Real-time analytics for hospital decision-makers with city-level demand heatmaps.', tag: 'For Hospitals' },
  { icon: '📚', title: 'Awareness Hub', desc: 'Myth-busting FAQs, legal guides and educational content all in one place.', tag: 'Education' },
]
const steps = [
  { icon: '✍️', title: 'Register', desc: 'Create an account and complete your donor profile with organ preferences.' },
  { icon: '✅', title: 'Get Verified', desc: 'Admin reviews and approves your profile with full audit trail.' },
  { icon: '📈', title: 'AI Analysis', desc: 'ML models analyse regional demand and generate instability reports.' },
  { icon: '❤️', title: 'Save Lives', desc: 'Your profile helps save up to 8 lives when the time comes.' },
]
</script>

<style scoped>
.home { overflow-x: hidden; }

/* Hero */
.hero {
  position: relative;
  background: var(--bg);
  padding: 80px 0 72px;
  border-bottom: 3px solid #000;
  overflow: hidden;
}
.hero-bg-blobs { display: none; }
.blob { display: none; }
.hero-inner {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 64px;
  align-items: center;
  position: relative;
}
.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: var(--accent);
  border: 2px solid #000;
  color: #000;
  padding: 7px 16px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 24px;
  box-shadow: 2px 2px 0 #000;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.badge-dot {
  width: 8px; height: 8px;
  border-radius: 2px;
  background: #000;
}
.hero-title {
  font-size: 52px;
  font-weight: 900;
  line-height: 1.05;
  letter-spacing: -0.04em;
  margin-bottom: 22px;
  color: var(--text);
}
.gradient-text {
  color: var(--primary);
  text-decoration: underline;
  text-underline-offset: 6px;
  text-decoration-thickness: 4px;
}
.hero-desc {
  font-size: 17px;
  color: var(--text-muted);
  line-height: 1.75;
  margin-bottom: 36px;
  max-width: 480px;
}
.hero-actions { display: flex; gap: 14px; flex-wrap: wrap; }

/* Hero stats */
.hero-stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.hero-stat-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 6px;
  padding: 24px;
  box-shadow: var(--shadow-md);
  text-align: center;
  transition: transform var(--transition), box-shadow var(--transition);
}
.hero-stat-card:hover { transform: translate(-2px,-2px); box-shadow: var(--shadow-lg); }
.hero-stat-icon { font-size: 28px; margin-bottom: 10px; }
.hero-stat-value { font-size: 30px; font-weight: 900; color: var(--primary); letter-spacing: -0.02em; }
.hero-stat-label { font-size: 13px; color: var(--text-muted); font-weight: 700; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.04em; }

/* Features */
.features-section { padding: 80px 0; background: var(--bg); border-bottom: 3px solid #000; }
.section-header { text-align: center; margin-bottom: 52px; }
.section-eyebrow {
  display: inline-block;
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #fff;
  background: var(--primary);
  border: 2px solid #000;
  padding: 4px 12px;
  margin-bottom: 16px;
  box-shadow: 2px 2px 0 #000;
}
.section-title { font-size: 36px; font-weight: 900; letter-spacing: -0.03em; margin-bottom: 14px; }
.section-sub { font-size: 15px; color: var(--text-muted); max-width: 520px; margin: 0 auto; font-weight: 500; }
.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}
.feature-card {
  background: #fff;
  border: 2px solid #000;
  border-radius: 6px;
  padding: 28px;
  box-shadow: var(--shadow-md);
  transition: transform var(--transition), box-shadow var(--transition);
  position: relative;
  overflow: hidden;
}
.feature-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 5px;
  background: var(--accent);
  border-bottom: 2px solid #000;
}
.feature-card:hover { transform: translate(-2px,-2px); box-shadow: var(--shadow-lg); }
.feature-icon-wrap { font-size: 34px; margin-bottom: 16px; margin-top: 8px; }
.feature-card h3 { font-size: 15px; font-weight: 800; margin-bottom: 10px; color: var(--text); }
.feature-card p { font-size: 14px; color: var(--text-muted); line-height: 1.6; margin-bottom: 16px; font-weight: 500; }
.feature-tag {
  display: inline-block;
  background: var(--accent);
  color: #000;
  border: 1.5px solid #000;
  border-radius: 3px;
  font-size: 11px;
  font-weight: 800;
  padding: 3px 10px;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

/* How it works */
.how-section { padding: 80px 0; background: var(--bg-subtle); border-bottom: 3px solid #000; }
.steps-row {
  display: flex;
  gap: 0;
  margin-top: 52px;
  position: relative;
}
.step-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  position: relative;
}
.step-connector {
  position: absolute;
  top: 29px;
  left: -50%;
  width: 100%;
  height: 3px;
  background: #000;
  z-index: 0;
}
.step-bubble {
  width: 58px; height: 58px;
  border-radius: 4px;
  background: var(--accent);
  border: 2px solid #000;
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  margin-bottom: 20px;
  position: relative;
  z-index: 1;
  box-shadow: var(--shadow);
  transition: transform var(--transition), box-shadow var(--transition);
}
.step-item:hover .step-bubble {
  transform: translate(-2px,-2px);
  box-shadow: var(--shadow-lg);
}
.step-num { font-size: 10px; font-weight: 800; color: var(--primary); text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 8px; display: block; }
.step-info h3 { font-size: 15px; font-weight: 800; margin-bottom: 8px; color: var(--text); }
.step-info p { font-size: 13px; color: var(--text-muted); line-height: 1.55; max-width: 160px; margin: 0 auto; font-weight: 500; }

/* Insight Strip */
.insight-strip {
  background: var(--primary);
  border-top: 3px solid #000;
  border-bottom: 3px solid #000;
  padding: 36px 0;
}
.insight-inner {
  display: flex;
  align-items: center;
  gap: 24px;
}
.insight-icon { font-size: 42px; flex-shrink: 0; }
.insight-inner h3 { font-size: 18px; font-weight: 800; color: #fff; margin-bottom: 6px; }
.insight-inner p { font-size: 14px; color: rgba(255,255,255,0.85); font-weight: 500; }
.insight-inner .btn { flex-shrink: 0; margin-left: auto; background:#fff; color:#000; border-color:#000; }

/* CTA */
.cta-section {
  position: relative;
  background: var(--accent);
  border-top: 3px solid #000;
  border-bottom: 3px solid #000;
  padding: 90px 0;
  text-align: center;
}
.cta-bg { display: none; }
.cta-inner { position: relative; z-index: 1; }
.cta-section h2 {
  font-size: 42px;
  font-weight: 900;
  color: #000;
  letter-spacing: -0.03em;
  margin-bottom: 16px;
}
.cta-section h2 span { background: var(--primary); color:#fff; padding: 2px 8px; display: inline-block; }
.cta-section p { font-size: 16px; color: #000; margin-bottom: 40px; font-weight: 600; opacity: 0.75; }
.cta-actions { display: flex; gap: 16px; justify-content: center; flex-wrap: wrap; }

@media (max-width: 1024px) {
  .hero-inner { grid-template-columns: 1fr; text-align: center; gap: 40px; }
  .hero-desc { max-width: 100%; margin: 0 auto 36px; }
  .hero-actions { justify-content: center; }
  .hero-stats-grid { grid-template-columns: repeat(4, 1fr); }
  .features-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 768px) {
  .hero { padding: 60px 0 52px; }
  .hero-title { font-size: 34px; }
  .hero-stats-grid { grid-template-columns: repeat(2, 1fr); }
  .features-grid { grid-template-columns: 1fr; }
  .steps-row { flex-direction: column; gap: 20px; }
  .step-connector { display: none; }
  .insight-inner { flex-direction: column; text-align: center; }
  .insight-inner .btn { margin-left: 0; }
  .cta-section h2 { font-size: 27px; }
}
</style>
