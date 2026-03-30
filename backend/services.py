"""
Service layer - Business logic separated from routes
Handles database operations, validation, and business rules
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
import logging
import hashlib

from models import (
    User,
    RecipientVerification,
    FileUpload,
    SessionToken,
    AuditLog,
)
from auth import hash_password, verify_password
from security import TokenManager
from config import settings

logger = logging.getLogger(__name__)


class AuthService:
    """Handle authentication operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_user(self, email: str, password: str, full_name: str, role: str):
        """Register a new user"""
        # Check existing user
        result = await self.db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise ValueError("Email already registered")

        # Create user
        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=role,
        )
        self.db.add(user)
        await self.db.flush()

        # Audit log
        await self._audit_log(user.id, "USER_REGISTERED", {"email": email})
        await self.db.commit()

        return user

    async def authenticate_user(self, email: str, password: str, ip_address: str, user_agent: str):
        """Authenticate user and create session"""
        result = await self.db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(password, user.hashed_password):
            await self._audit_log(None, "LOGIN_FAILED", {"email": email, "ip": ip_address})
            raise ValueError("Invalid credentials")

        # Create tokens
        access_token = TokenManager.create_access_token(
            data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else str(user.role)},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        
        refresh_token = TokenManager.create_refresh_token(
            data={"sub": str(user.id), "role": user.role.value if hasattr(user.role, 'value') else str(user.role)},
            expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )

        # Store session
        session = SessionToken(
            user_id=user.id,
            refresh_token_hash=hashlib.sha256(refresh_token.encode()).hexdigest(),
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
        )
        self.db.add(session)

        await self._audit_log(user.id, "USER_LOGIN", {"ip": ip_address})
        await self.db.commit()

        return {
            "user_id": str(user.id),
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

    async def refresh_access_token(self, user_id: str, refresh_token: str):
        """Generate new access token from refresh token"""
        # Verify token
        payload = TokenManager.verify_token(refresh_token, token_type="refresh")

        # Check session exists and not revoked
        result = await self.db.execute(
            select(SessionToken).where(
                and_(
                    SessionToken.user_id == user_id,
                    SessionToken.is_revoked == False,
                    SessionToken.expires_at > datetime.utcnow(),
                )
            )
        )
        session = result.scalar_one_or_none()
        if not session:
            raise ValueError("Session expired or invalid")

        # Get user
        user_result = await self.db.execute(select(User).where(User.id == user_id))
        user = user_result.scalar_one_or_none()

        # Create new access token
        access_token = TokenManager.create_access_token(
            data={"sub": str(user.id), "role": user.role},
            expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )

        # Update session
        session.last_used_at = datetime.utcnow()
        await self.db.commit()

        return {"access_token": access_token}

    async def logout(self, user_id: str):
        """Revoke all user sessions"""
        result = await self.db.execute(
            select(SessionToken).where(SessionToken.user_id == user_id)
        )
        sessions = result.scalars().all()

        for session in sessions:
            session.is_revoked = True

        await self._audit_log(user_id, "USER_LOGOUT")
        await self.db.commit()

    async def _audit_log(self, user_id: Optional[str], action: str, details: dict = None):
        """Create audit log entry"""
        log = AuditLog(
            user_id=user_id,
            action=action,
            details=details or {},
        )
        self.db.add(log)


class RecipientService:
    """Handle recipient verification operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_verification(self, user_id: str) -> Optional[RecipientVerification]:
        """Get recipient verification record"""
        result = await self.db.execute(
            select(RecipientVerification).where(RecipientVerification.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_verification(self, user_id: str) -> RecipientVerification:
        """Create new verification record"""
        verification = RecipientVerification(user_id=user_id)
        self.db.add(verification)
        await self.db.commit()
        return verification

    async def save_step_data(
        self, user_id: str, step: int, data: dict
    ) -> RecipientVerification:
        """Save data for specific step"""
        verification = await self.get_verification(user_id)
        if not verification:
            verification = await self.create_verification(user_id)

        # Update based on step
        if step == 1:  # Personal details
            verification.phone = data.get("phone")
            verification.address = data.get("address")
            verification.dob = data.get("dob")
        elif step == 2:  # Medical history
            verification.medical_condition = data.get("condition")
            verification.transplant_type = data.get("transplantType")
            verification.medical_notes = data.get("notes")
        elif step == 3:  # Documents
            verification.documents = data.get("documents", {})
        elif step == 4:  # Hospital reference
            verification.hospital_name = data.get("name")
            verification.hospital_contact = data.get("contact")
            verification.hospital_city = data.get("city")
        elif step == 5:  # Consent
            verification.consent_agreed = data.get("agreed", False)
            verification.consent_date = data.get("date")

        verification.current_step = step
        verification.status = "in_progress"
        verification.updated_at = datetime.utcnow()

        await self.db.commit()
        return verification

    async def submit_verification(self, user_id: str) -> RecipientVerification:
        """Submit completed verification"""
        verification = await self.get_verification(user_id)
        if not verification:
            raise ValueError("Verification not found")

        # Validate all required fields
        if not all([
            verification.phone,
            verification.address,
            verification.dob,
            verification.medical_condition,
            verification.transplant_type,
            verification.hospital_name,
            verification.consent_agreed,
        ]):
            raise ValueError("Missing required fields")

        verification.status = "submitted"
        verification.submitted_at = datetime.utcnow()
        verification.updated_at = datetime.utcnow()

        await self.db.commit()
        return verification

    async def get_verification_summary(self, user_id: str) -> dict:
        """Get verification data as summary"""
        verification = await self.get_verification(user_id)
        if not verification:
            return {}

        return {
            "status": verification.status,
            "submitted_at": verification.submitted_at.isoformat() if verification.submitted_at else None,
            "personal": {
                "phone": verification.phone,
                "address": verification.address,
                "dob": verification.dob,
            },
            "medical": {
                "condition": verification.medical_condition,
                "transplant_type": verification.transplant_type,
                "notes": verification.medical_notes,
            },
            "hospital": {
                "name": verification.hospital_name,
                "contact": verification.hospital_contact,
                "city": verification.hospital_city,
            },
            "consent": {
                "agreed": verification.consent_agreed,
                "date": verification.consent_date,
            },
        }


class FileService:
    """Handle secure file operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def validate_file(self, file_size: int, mime_type: str):
        """Validate file before upload"""
        # Check size
        if file_size > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
            raise ValueError(f"File too large (max {settings.MAX_FILE_SIZE_MB}MB)")

        # Check MIME type
        if mime_type not in settings.ALLOWED_MIME_TYPES:
            raise ValueError(f"File type not allowed: {mime_type}")

    async def create_file_record(
        self,
        user_id: str,
        filename: str,
        file_type: str,
        mime_type: str,
        file_size: int,
        file_url: str,
        verification_id: Optional[str] = None,
    ) -> FileUpload:
        """Create file upload record"""
        file_upload = FileUpload(
            user_id=user_id,
            verification_id=verification_id,
            filename=filename,
            original_filename=filename.split("/")[-1],
            file_type=file_type,
            mime_type=mime_type,
            file_size=file_size,
            file_url=file_url,
        )
        self.db.add(file_upload)
        await self.db.commit()
        return file_upload

    async def get_user_files(self, user_id: str) -> List[FileUpload]:
        """Get all files uploaded by user"""
        result = await self.db.execute(
            select(FileUpload).where(FileUpload.user_id == user_id)
        )
        return result.scalars().all()
