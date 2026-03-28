# 🫀 LifeLink AI

**India's First Intelligent Organ Donation Platform** — powered by XGBoost, SHAP, and a real-time decision-support pipeline.

> Built with Vue 3 + FastAPI + Neon PostgreSQL · NeoBrutalism UI · Explainable AI

---

## ✨ Features

| Feature | Description |
|---|---|
|  🩸 **Donor Registration** | Multi-step digital registration with organ preferences, consent and status tracking |
| 🤖 **AI Demand Forecasting** | XGBoost model trained on 55 real Indian city survey responses; 3–6 month projections |
| 📊 **ODII Index** | Organ Demand Instability Index — novel research metric quantifying regional shortage risk |
| 🔍 **Explainable AI** | SHAP-based transparency; understand exactly *why* each prediction is made |
| 🏥 **Hospital Dashboard** | Real-time analytics with city-level demand heatmaps and ODII tables |
| 📚 **Awareness Hub** | Myth-busting FAQs, legal guides and educational content |
| 🛡️ **Admin Portal** | User management, donor approval workflow, ML training triggers |

---

## 🛠️ Tech Stack

**Frontend**
- Vue 3 · Vite 5 · Vue Router · Pinia
- Chart.js · Vue-ChartJS
- NeoBrutalism Design System (Space Grotesk)
- Marked.js (Markdown rendering for AI)

**Backend**
- FastAPI · Uvicorn
- SQLAlchemy 2 · AsyncPG · Neon PostgreSQL (serverless)
- JWT Authentication (python-jose + passlib)
- Groq Cloud SDK (Llama 3.1 8B)
- SlowAPI (Rate limiting)

**ML Pipeline**
- XGBoost · scikit-learn · SHAP
- Pandas · NumPy · Joblib
- Fairness & Calibration Evaluation
- Model Versioning System
- Trained on `Organ Donation.csv` (55 Indian city survey responses)

---

## 🚀 Quick Start (One Click)

### Prerequisites
- Python 3.10+ — [python.org](https://python.org)
- Node.js 18+ — [nodejs.org](https://nodejs.org)
- A [Neon](https://neon.tech) PostgreSQL database (free tier works)

### 1 · Configure environment

Copy and fill in the backend environment file:

```
backend\.env
```

```env
DATABASE_URL=postgresql://<user>:<password>@<host>/<db>?sslmode=require
JWT_SECRET=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
APP_NAME=LifeLink AI
DEBUG=True

# Required for AI Chatbot (get it at console.groq.com)
GROQ_API_KEY=gsk_your_key_here

# Required for AI Chatbot (Get at console.groq.com)
GROQ_API_KEY=gsk_...
```

### 2 · Run everything in one click

```bat
start.bat
```

This script will:
1. Create a Python virtual environment (`.venv`) if one doesn't exist
2. Install all Python dependencies from `backend/requirements.txt`
3. Install all Node.js dependencies in `frontend/`
4. Launch the **FastAPI backend** on `http://localhost:8000`
5. Launch the **Vue frontend** on `http://localhost:5173`

Both servers open in separate windows and run concurrently.

---

## 🔧 Manual Setup

### Backend

```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

# Install dependencies
pip install -r backend/requirements.txt

# Seed the database (optional demo data)
cd backend
python seed.py

# Start backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App will be available at **http://localhost:5173**

---

## 🌐 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register new user |
| POST | `/auth/login` | Get JWT token |
| GET | `/donors/me` | Current donor profile |
| PUT | `/donors/me` | Update donor profile |
| GET | `/admin/analytics` | Admin statistics |
| GET | `/admin/donors` | All donors list |
| PUT | `/admin/donors/{id}/approve` | Approve donor |
| POST | `/ml/train` | Trigger ML training |
| GET | `/ml/metrics` | Model performance metrics |
| GET | `/ml/forecast` | Regional demand forecast |
| GET | `/ml/odii` | ODII index data |
| GET | `/ml/shap` | SHAP feature importance |
| GET | `/ml/fairness` | Bias & fairness metrics |
| GET | `/ml/calibration` | Model reliability scores |
| POST | `/chat` | AI Assistant interaction |
| GET | `/admin/chat-logs` | User interaction history |
| GET | `/admin/model-versions` | Training version history |

Interactive API docs: **http://localhost:8000/docs**

---

## 📁 Project Structure

```
Organ/
├── start.bat                   ← One-click launcher
├── .gitignore
├── README.md
├── Organ Donation.csv          ← Training dataset
│
├── backend/
│   ├── main.py                 ← FastAPI app entry point
│   ├── auth.py                 ← JWT auth utilities
│   ├── models.py               ← SQLAlchemy models
│   ├── database.py             ← DB connection
│   ├── config.py               ← Settings (pydantic)
│   ├── ml_pipeline.py          ← XGBoost + SHAP pipeline
│   ├── seed.py                 ← Demo data seeder
│   ├── requirements.txt
│   ├── .env                    ← ⚠️ Not committed (see .gitignore)
│   └── routers/
│       ├── auth.py
│       ├── donors.py
│       ├── admin.py
│       └── ml.py
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.js
        ├── App.vue
        ├── assets/
        │   └── style.css       ← Global NeoBrutalism design system
        ├── stores/
        │   └── auth.js         ← Pinia auth store
        ├── router/
        │   └── index.js
        ├── components/
        │   └── Navbar.vue
        └── views/
            ├── Home.vue
            ├── Login.vue
            ├── Register.vue
            ├── DonorDashboard.vue
            ├── HospitalDashboard.vue
            ├── AdminDashboard.vue
            ├── MLDashboard.vue
            └── Awareness.vue
```

---

## 🤖 ML Pipeline

1. **Data** — `Organ Donation.csv`: 55 real responses from Indian cities (age, blood group, religion, family support, etc.)
2. **Preprocessing** — Label encoding, feature scaling, train/test split
3. **Model** — XGBoost classifier (63.6% accuracy on hold-out set)
4. **ODII** — Custom instability index: `(projected_demand - supply) / supply` weighted by regional donor density
5. **SHAP** — TreeExplainer generates per-prediction feature attribution; surfaced in the ML Dashboard
6. **Forecast** — 3–6 month city-level demand projections saved to the database on each training run

---

## 🧪 Demo Accounts

After running `python seed.py`:

| Role | Email | Password |
|------|-------|----------|
| Admin | `admin@lifelink.ai` | `admin123` |
| Hospital | `hospital@apollo.com` | `hospital123` |
| Donor | `donor@example.com` | `donor123` |

---

## 📄 License

MIT — free to use, modify and distribute.

---

*Made with ❤️ — because every second matters.*

