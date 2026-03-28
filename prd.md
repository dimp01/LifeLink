# Project Name

# **LifeLink AI – Intelligent Organ Donation Decision Support System**

---

# 1. Executive Summary

LifeLink AI is a **cloud-native, AI-powered organ donation platform** designed for:

* Digital donor registration
* Organ donation awareness & myth clearing
* ML-based organ demand forecasting
* Regional instability risk scoring
* Explainable AI insights
* Hospital decision-support analytics

The system must be:

* Python-first
* Minimal tech stack
* Single cloud database
* Research publishable
* SaaS structured
* Secure and scalable

---

# 2. Technology Stack (STRICT REQUIREMENT)

## Backend

* **FastAPI (Python 3.10+)**
* Pydantic for validation
* SQLAlchemy or asyncpg for DB

## Frontend

* **Vue 3 (Vite)**
* Axios or Fetch API
* Minimal component architecture
* No heavy UI frameworks required

## Database

* **Neon PostgreSQL (Cloud Managed)**
* Use **pgvector extension** for vector storage (if embeddings needed)

## Authentication

* Custom JWT-based auth
* Passlib (bcrypt)
* PyJWT
* Role-based access control

## ML

* Pandas
* Scikit-learn / XGBoost
* SHAP (Explainable AI)
* Joblib for model persistence

## Deployment

* Railway OR Render
* No Docker

---

# 3. System Architecture

```
Vue 3 Frontend
        ↓
FastAPI Backend
        ↓
Neon PostgreSQL (Single Database)
        ↓
ML Models (loaded inside backend)
```

Single service.
Single database.
No microservices.
No containerization.

---

# 4. User Roles

## 1. Donor

* Register & Login
* Submit donor profile
* View status
* Access awareness content

## 2. Hospital Admin

* Login
* View anonymized analytics
* View demand forecasting dashboard
* Access instability index

## 3. Super Admin

* Approve/reject donors
* Trigger ML training
* View system analytics
* Manage awareness content

---

# 5. Core Functional Modules

---

## 5.1 Authentication Module (JWT Based)

### Features:

* POST /register
* POST /login
* JWT access token generation
* Token validation middleware
* Role-based route protection
* Password hashing (bcrypt)
* Secure token expiration

---

## 5.2 Donor Registration Module

Multi-step Vue form:

Fields:

* Full name
* Age
* Blood group
* Location (Region/State)
* Organs willing to donate
* Medical history (optional)
* Emergency contact
* Consent agreement

Database:

* Linked to user_id
* Status: Pending / Approved / Rejected

---

## 5.3 Awareness & Myth Clearing Module

Dynamic content from database:

* Myth vs Fact
* Legal procedure
* FAQ
* Religious neutrality
* Educational articles

Admin can create/edit content.

---

# 6. ML Intelligence Module (RESEARCH CORE)

This is the primary innovation.

---

## 6.1 CSV Usage

The provided CSV dataset must be used to:

* Clean and preprocess data
* Perform feature engineering
* Train predictive model
* Store model metrics
* Generate forecasts
* Save predictions in database

---

## 6.2 ML Objectives

### Model 1: Organ Demand Forecasting

Predict:

* Future organ demand per region
* 3–6 month projection
* Organ-wise trend patterns

Suggested Models:

* Random Forest
* XGBoost
* ARIMA (for time-series)
* LSTM (optional advanced)

---

### Model 2: Organ Demand Instability Index (ODII)

Define custom metric:

```
ODII = (Projected Demand − Available Supply) / Registered Donors
```

Store ODII per region and organ.

This is your research contribution.

---

### Model 3: Explainable AI

Use SHAP to:

* Show feature importance
* Explain prediction reasoning
* Display explanation data via API
* Provide interpretation dashboard

---

# 7. Analytics Dashboard (Vue)

Hospital/Admin dashboard must include:

* Organ-wise demand chart
* Region-wise demand heatmap
* ODII index visualization
* Prediction confidence scores
* SHAP explanation summaries
* Historical trend graphs

Use simple chart library (e.g., Chart.js).

---

# 8. Database Schema (Single PostgreSQL)

## users

* id (UUID, PK)
* email (unique)
* hashed_password
* role (donor/hospital/admin)
* created_at

## donors

* id
* user_id (FK)
* age
* blood_group
* location
* organs_selected (JSON)
* medical_history
* status
* created_at

## ml_predictions

* id
* region
* organ_type
* predicted_demand
* instability_index
* confidence_score
* created_at

## awareness_content

* id
* title
* content
* type (myth/faq/blog/legal)

## audit_logs

* id
* user_id
* action
* timestamp

---

# 9. API Endpoints

## Authentication

* POST /auth/register
* POST /auth/login
* GET /auth/me

## Donor

* POST /donor
* GET /donor/me
* PUT /donor/update

## ML

* POST /ml/train
* GET /ml/predict
* GET /ml/instability-index
* GET /ml/explain

## Admin

* GET /admin/donors
* GET /admin/analytics
* POST /admin/awareness

## Awareness

* GET /awareness
* GET /awareness/{type}

---

# 10. Research Deliverables

System must support:

* Exportable model metrics (MAE, RMSE, R²)
* Bias evaluation metrics
* Feature importance logs
* Instability index reporting
* Academic documentation support

---

# 11. Non-Functional Requirements

* API latency < 500ms
* Secure JWT validation
* Input validation via Pydantic
* Clean modular structure
* Environment-based config
* SQL injection prevention
* Error handling middleware

---

# 12. Folder Structure Requirement

Backend:

```
backend/
│
├── main.py
├── database.py
├── models.py
├── auth.py
├── ml_pipeline.py
├── routers/
│   ├── auth.py
│   ├── donor.py
│   ├── admin.py
│   └── ml.py
└── requirements.txt
```

Frontend:

```
frontend/
│
├── src/
│   ├── components/
│   ├── views/
│   ├── router/
│   └── services/api.js
```

---

# 13. Constraints

* Single database only
* No Docker
* Python backend only
* Cloud PostgreSQL only
* Must integrate ML from CSV
* Must remain research-oriented

---

# 14. Success Criteria

* Functional donor registration
* Secure JWT authentication
* CSV-based ML training pipeline
* ODII calculation working
* Dashboard displaying forecasts
* Explainable AI outputs visible
* Cloud deployable

---

# 15. Research Positioning Statement

The system should be framed as:

> A Cloud-Native AI-Driven Organ Demand Forecasting and Decision Support Platform Using Explainable Machine Learning.


5.1 Objective

Implement a controlled LLM-based chatbot that:

Answers ONLY organ donation queries

Rejects unrelated questions

Provides myth clarification

Avoids diagnosis and prescriptions

Logs interactions for research

5.2 Architecture

User → Vue Chat UI
↓
FastAPI /chat endpoint
↓
Query Classification Model
↓
If organ-related → Groq API
Else → Reject
↓
Response returned
↓
Log stored in DB

5.3 Query Classification Layer (Mandatory)

Train lightweight classifier:

TF-IDF + Logistic Regression

Labels:

organ_related

non_organ_related

Reject if non-organ-related.

5.4 Groq System Prompt

System prompt must enforce:

Organ donation only

No general knowledge

No medical prescriptions

No diagnosis

Suggest consulting doctors

Educational tone only

5.5 Chat Logging

Table: chat_logs

Fields:

id

user_id (nullable)

query

classification

response

confidence

timestamp

Used for:

Research evaluation

Model refinement

Bias study

5.6 Optional RAG Upgrade

Store awareness content in DB

Retrieve relevant entries

Send context + query to Groq

Reduce hallucination

6. NEW MODULE – Fairness & Bias Evaluation

Since dataset includes religion, age, etc.

System must compute:

Prediction distribution by religion

Demand prediction variance by region

False positive rate by demographic

Feature dominance analysis

Expose via:

GET /ml/fairness

7. NEW MODULE – Model Versioning

Table: model_versions

id

training_date

accuracy

hyperparameters

dataset_hash

notes

Every training run must:

Create new model version entry

Store metrics

Link forecasts to version_id

8. NEW MODULE – Confidence & Calibration

System must compute:

Probability confidence

Calibration curve data

Reliability score

Expose via:
GET /ml/calibration

9. Analytics Dashboard Enhancements

Add:

Chat usage stats

ODII trend over time

Model accuracy history

Forecast confidence

Fairness metrics

Version comparison

10. Security Enhancements

Rate limiting per user

API key protection (Groq)

Input validation

CORS restriction

Logging middleware

11. API Additions

Chat:
POST /chat

ML:
GET /ml/fairness
GET /ml/calibration
GET /ml/version-history

Admin:
GET /admin/chat-logs
GET /admin/model-versions

12. Research Contribution Positioning

The system demonstrates:

AI-driven organ demand forecasting

Novel ODII instability metric

Explainable ML transparency

Domain-constrained medical LLM architecture

Guardrail-based chatbot filtering

Bias-aware predictive analytics

Cloud-native deployment model

13. Success Criteria

System is complete when:

Chatbot rejects unrelated questions

Forecasting works reliably

ODII stored historically

SHAP explanations visible

Model versions tracked

Fairness metrics computed

All dashboards functional

Fully deployable on cloud
