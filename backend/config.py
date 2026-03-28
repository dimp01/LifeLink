from typing import Optional, List
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str
        
    # Security & JWT
    SECRET_KEY: str = Field(
        default="lifelink-ai-super-secret-jwt-key-2026-xK9mP3nQ7rT5vW2z",
        alias="JWT_SECRET"
    )
    ALGORITHM: str = Field(
        default="HS256",
        alias="JWT_ALGORITHM"
    )
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  # Short-lived access tokens
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7     # Long-lived refresh tokens
    
    # Cookies
    COOKIE_SECURE: bool = True             # HTTPS only in production
    COOKIE_HTTPONLY: bool = True           # No JS access
    COOKIE_SAMESITE: str = "Lax"           # CSRF protection
    COOKIE_DOMAIN: Optional[str] = None    # Set in production
    SESSION_COOKIE_NAME: str = "session"   # Session cookie name
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = 100         # Per user/IP per window
    RATE_LIMIT_PER_MINUTE: int = 30        # Global
    RATE_LIMIT_PER_USER: int = 100         # Per user
    RATE_LIMIT_WINDOW: int = 60            # seconds
    
    # File Upload
    MAX_FILE_SIZE_MB: int = 20              # Max 20MB per file
    ALLOWED_MIME_TYPES: List[str] = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
    ]
    UPLOAD_DIR: str = "uploads"
    S3_BUCKET: Optional[str] = None         # For object storage
    S3_REGION: Optional[str] = None
    S3_ACCESS_KEY: Optional[str] = None
    S3_SECRET_KEY: Optional[str] = None
    APP_NAME: str = "LifeLink AI"
    DEBUG: bool = False
    GROQ_API_KEY: str = ""
    RATE_LIMIT_PER_MINUTE: int = 30

    class Config:
        env_file = ".env"
        populate_by_name = True  # Allow both field name and alias


settings = Settings()

