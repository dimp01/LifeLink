from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text

from database import engine, Base
from routers import auth, donor, admin, ml, awareness, recipient, file_upload, chat, campaigns, community, hospital, tracking, matching
from middleware import (
    RateLimitMiddleware,
    CSRFMiddleware,
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
)


limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

        # Ensure Postgres enum has been updated with the new role (added in app code)
        # Postgres enums are not auto-migrated by SQLAlchemy, so we safely attempt
        # to add the value if it's missing.
        try:
            await conn.execute(text("ALTER TYPE userrole ADD VALUE 'recipient'"))
        except Exception:
            # Ignore errors from already-existing value or missing enum type.
            pass

    yield


app = FastAPI(
    title="LifeLink AI",
    description="Intelligent Organ Donation Decision Support System",
    version="2.0.0",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS - MUST be first middleware added (it's applied last due to middleware stack reversal)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https://.*\.app\.github\.dev$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security and logging middleware
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
# app.add_middleware(CSRFMiddleware)

# Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(donor.router, prefix="/donor", tags=["Donor"])
app.include_router(admin.router, prefix="/admin", tags=["Admin"])
app.include_router(ml.router, prefix="/ml", tags=["ML"])
app.include_router(matching.router, prefix="/ml", tags=["ML Matching"])
app.include_router(awareness.router, prefix="/awareness", tags=["Awareness"])
app.include_router(recipient.router, tags=["Recipient"])
app.include_router(file_upload.router, tags=["File Upload"])
app.include_router(chat.router, prefix="/chat", tags=["Chat"])
app.include_router(campaigns.router, tags=["Campaigns"])
app.include_router(community.router, tags=["Community"])
app.include_router(hospital.router, tags=["Hospital"])
app.include_router(tracking.router, tags=["Tracking"])


@app.get("/", tags=["Root"])
async def root():
    return {"message": "LifeLink AI API is running", "version": "2.0.0"}


@app.get("/health", tags=["Root"])
async def health():
    return {"status": "healthy"}
