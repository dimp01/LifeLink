"""
Chat Router – Domain-Constrained LLM Chatbot
Uses TF-IDF + Logistic Regression to classify queries before forwarding to Groq.
Only organ-donation-related queries are answered.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import joblib
import os
from pathlib import Path

from database import get_db
from models import ChatLog
from config import settings

router = APIRouter()

# ──────────────────────────────────────────────
# CLASSIFIER SETUP (TF-IDF + Logistic Regression)
# ──────────────────────────────────────────────

MODEL_DIR = Path(__file__).parent.parent / "ml_models"
CLASSIFIER_PATH = MODEL_DIR / "chat_classifier.pkl"

# Seed training data
_TRAIN_DATA = [
    # organ_related
    ("What is organ donation?", "organ_related"),
    ("How do I register as an organ donor?", "organ_related"),
    ("Which organs can be donated after death?", "organ_related"),
    ("Is organ donation allowed in Islam?", "organ_related"),
    ("Is organ donation allowed in Hinduism?", "organ_related"),
    ("Is organ donation allowed in Christianity?", "organ_related"),
    ("What are the myths about organ donation?", "organ_related"),
    ("Can a diabetic donate organs?", "organ_related"),
    ("How many lives can one organ donor save?", "organ_related"),
    ("What is the process of organ donation?", "organ_related"),
    ("Who can be an organ donor?", "organ_related"),
    ("What organs and tissues can be donated?", "organ_related"),
    ("Can old people donate organs?", "organ_related"),
    ("Is there an age limit for organ donation?", "organ_related"),
    ("Will organ donation disfigure my body?", "organ_related"),
    ("Does organ donation affect funeral arrangements?", "organ_related"),
    ("Is organ donor registration free?", "organ_related"),
    ("How does organ matching work?", "organ_related"),
    ("What is brain death?", "organ_related"),
    ("Can living people donate organs?", "organ_related"),
    ("What is a deceased donor?", "organ_related"),
    ("How long does transplant surgery take?", "organ_related"),
    ("What are the waiting lists for organ transplant?", "organ_related"),
    ("Do rich patients get priority in organ allocation?", "organ_related"),
    ("Can donors specify which organs to donate?", "organ_related"),
    ("What happens after I register as donor?", "organ_related"),
    ("How do I tell my family about organ donation?", "organ_related"),
    ("Organ donation awareness campaign", "organ_related"),
    ("Kidney transplant procedure", "organ_related"),
    ("heart liver lungs transplant", "organ_related"),
    ("eye cornea donation", "organ_related"),
    ("blood donation difference organ donation", "organ_related"),
    ("organ donation statistics India", "organ_related"),
    ("NOTTO national organ transplant", "organ_related"),
    ("organ donation consent form", "organ_related"),
    ("transplant rejection risk", "organ_related"),
    ("post transplant care", "organ_related"),
    # non_organ_related
    ("What is the weather today?", "non_organ_related"),
    ("Tell me a joke", "non_organ_related"),
    ("What is the capital of France?", "non_organ_related"),
    ("How do I cook pasta?", "non_organ_related"),
    ("Who won the cricket match?", "non_organ_related"),
    ("What is machine learning?", "non_organ_related"),
    ("Write me a poem", "non_organ_related"),
    ("How to invest in stocks?", "non_organ_related"),
    ("What movies are popular?", "non_organ_related"),
    ("Tell me about politics", "non_organ_related"),
    ("How to lose weight?", "non_organ_related"),
    ("What is the best diet plan?", "non_organ_related"),
    ("Help me with my homework", "non_organ_related"),
    ("What is 2+2?", "non_organ_related"),
    ("Recommend a good book", "non_organ_related"),
    ("How do I fix my car?", "non_organ_related"),
    ("Python programming tips", "non_organ_related"),
    ("COVID vaccine side effects", "non_organ_related"),
    ("How to treat diabetes?", "non_organ_related"),
    ("What is the stock price of Apple?", "non_organ_related"),
    ("Online shopping deals", "non_organ_related"),
    ("How to play guitar?", "non_organ_related"),
    ("Sports news today", "non_organ_related"),
    ("What is blockchain?", "non_organ_related"),
    ("Travel tips for Europe", "non_organ_related"),
    ("How do I get a visa?", "non_organ_related"),
    ("Best smartphones 2025", "non_organ_related"),
    ("How to meditate?", "non_organ_related"),
    ("Talk to me", "non_organ_related"),
    ("Tell me something funny", "non_organ_related"),
]


def _build_classifier():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    texts = [x[0] for x in _TRAIN_DATA]
    labels = [x[1] for x in _TRAIN_DATA]

    clf = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
        ("lr", LogisticRegression(max_iter=1000, C=5.0, random_state=42)),
    ])
    clf.fit(texts, labels)
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(clf, CLASSIFIER_PATH)
    return clf


def get_classifier():
    """Load classifier from disk or train if not present."""
    if CLASSIFIER_PATH.exists():
        return joblib.load(CLASSIFIER_PATH)
    return _build_classifier()


# Pre-load at import time (non-blocking)
_clf = None


def _get_clf():
    global _clf
    if _clf is None:
        _clf = get_classifier()
    return _clf


# ──────────────────────────────────────────────
# GROQ CLIENT
# ──────────────────────────────────────────────

GROQ_SYSTEM_PROMPT = """You are LifeLink AI Assistant – a specialized educational chatbot focused exclusively on organ donation and transplantation.

Your rules:
1. ONLY answer questions about organ donation, transplantation, donor registration, myths/facts about organ donation, religious views on organ donation, post-transplant care, and related awareness topics.
2. Do NOT answer general knowledge, medical diagnosis, prescriptions, or unrelated topics.
3. Do NOT provide specific medical diagnoses or prescriptions.
4. Always suggest consulting a certified medical professional or transplant coordinator for specific medical decisions.
5. Maintain an educational, empathetic, and factual tone.
6. Keep responses concise, clear, and helpful.
7. If the user asks for something outside organ donation, politely redirect them to organ donation topics."""

REJECTION_MESSAGE = (
    "I'm LifeLink AI, specialized in organ donation information only. "
    "Your question appears to be outside this domain. "
    "Please ask me about organ donation, donor registration, transplantation, or related awareness topics."
)


async def call_groq(query: str, history: list = None) -> str:
    """Call Groq API with organ-donation system prompt and full conversation history."""
    if not settings.GROQ_API_KEY:
        raise HTTPException(status_code=503, detail="Groq API key not configured.")

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=settings.GROQ_API_KEY)

        messages = [{"role": "system", "content": GROQ_SYSTEM_PROMPT}]

        # Append prior turns (capped at last 10 exchanges = 20 messages)
        if history:
            for turn in history[-20:]:
                role = turn.get("role")   # "user" or "assistant"
                text = turn.get("text", "")
                if role in ("user", "assistant") and text:
                    messages.append({"role": role, "content": text})

        # Append current query
        messages.append({"role": "user", "content": query})

        completion = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=512,
            temperature=0.4,
        )
        return completion.choices[0].message.content.strip()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Groq API error: {str(e)}")


# ──────────────────────────────────────────────
# SCHEMAS
# ──────────────────────────────────────────────

from typing import Optional, List


class HistoryMessage(BaseModel):
    role: str   # "user" or "assistant"
    text: str


class ChatRequest(BaseModel):
    query: str
    user_id: Optional[str] = None
    history: Optional[List[HistoryMessage]] = []


class ChatResponse(BaseModel):
    response: str
    classification: str
    confidence: float
    timestamp: str


# ──────────────────────────────────────────────
# ENDPOINT
# ──────────────────────────────────────────────

@router.post("", response_model=ChatResponse)
async def chat(
    request: Request,
    payload: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    query = payload.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Classify query
    clf = _get_clf()
    proba = clf.predict_proba([query])[0]
    classes = clf.classes_.tolist()
    pred_class = classes[int(proba.argmax())]
    confidence = float(proba.max())

    # Determine response
    if pred_class == "organ_related" or confidence < 0.70:
        history_dicts = [{"role": m.role, "text": m.text} for m in (payload.history or [])]
        response_text = await call_groq(query, history=history_dicts)
        classification = "organ_related"
    else:
        response_text = REJECTION_MESSAGE
        classification = "non_organ_related"

    # Resolve user_id
    import uuid as _uuid
    user_uuid = None
    if payload.user_id:
        try:
            user_uuid = _uuid.UUID(payload.user_id)
        except ValueError:
            pass

    # Log to DB
    log = ChatLog(
        user_id=user_uuid,
        query=query,
        classification=classification,
        response=response_text,
        confidence=round(confidence, 4),
        timestamp=datetime.utcnow(),
    )
    db.add(log)
    await db.commit()

    return ChatResponse(
        response=response_text,
        classification=classification,
        confidence=round(confidence, 4),
        timestamp=datetime.utcnow().isoformat(),
    )
