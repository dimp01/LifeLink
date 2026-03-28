"""
Enhanced security module for LifeLink
- Secure JWT token handling
- Cookie-based session management
- Rate limiting utilities
- CSRF protection
"""

from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenManager:
    """Manage JWT access and refresh tokens"""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)

    @staticmethod
    def create_access_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create short-lived access token (15 minutes)"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=15)

        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def create_refresh_token(
        data: dict,
        expires_delta: Optional[timedelta] = None,
    ) -> str:
        """Create long-lived refresh token (7 days)"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(days=7)

        to_encode.update({"exp": expire, "type": "refresh"})
        encoded_jwt = jwt.encode(
            to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
        )
        return encoded_jwt

    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> dict:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
            )
            # Verify token type
            if payload.get("type") != token_type:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type",
                )
            return payload
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )


class RateLimiter:
    """Per-user and per-IP rate limiting"""

    def __init__(self):
        self.requests = {}  # In production, use Redis

    def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """
        Check if request is within rate limit
        key: user_id or IP address
        limit: max requests per window
        window: time window in seconds
        """
        now = datetime.utcnow()
        if key not in self.requests:
            self.requests[key] = []

        # Remove old requests outside window
        self.requests[key] = [
            req_time
            for req_time in self.requests[key]
            if (now - req_time).total_seconds() < window
        ]

        if len(self.requests[key]) >= limit:
            return False

        self.requests[key].append(now)
        return True


# Global rate limiter (use Redis in production)
rate_limiter = RateLimiter()


def generate_csrf_token() -> str:
    """Generate CSRF token"""
    import secrets
    return secrets.token_urlsafe(32)


def verify_csrf_token(provided_token: str, stored_token: str) -> bool:
    """Verify CSRF token"""
    return provided_token == stored_token
