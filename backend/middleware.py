import logging
import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from security import verify_csrf_token

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Log the incoming request
        logger.info(f"{request.method} {request.url} - {request.client.host if request.client else 'unknown'}")

        response = await call_next(request)

        # Log the response
        process_time = time.time() - start_time
        logger.info(f"Response: {response.status_code} - {process_time:.3f}s")

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests = {}

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"

        # Simple in-memory rate limiting (for production, use Redis or similar)
        current_time = time.time()
        if client_ip not in self.requests:
            self.requests[client_ip] = []

        # Clean old requests
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if current_time - req_time < 60
        ]

        if len(self.requests[client_ip]) >= self.requests_per_minute:
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests"}
            )

        self.requests[client_ip].append(current_time)
        response = await call_next(request)
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip CSRF check for GET, HEAD, OPTIONS requests
        if request.method in ["GET", "HEAD", "OPTIONS"]:
            return await call_next(request)

        # Skip CSRF check for auth endpoints that don't require it
        if request.url.path.startswith("/auth/") and request.url.path not in ["/auth/login", "/auth/register"]:
            return await call_next(request)

        # For now, just check if CSRF token header is present
        # TODO: Implement proper CSRF token verification with server-side storage
        csrf_token = request.headers.get("X-CSRF-Token")
        if not csrf_token:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token missing"}
            )

        # Basic validation - token should be non-empty
        if len(csrf_token.strip()) == 0:
            return JSONResponse(
                status_code=403,
                content={"detail": "CSRF token invalid"}
            )

        response = await call_next(request)
        return response