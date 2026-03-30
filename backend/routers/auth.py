import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Cookie
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta

from database import get_db
from models import User, UserRole, AuditLog, Recipient, Hospital
from auth import hash_password, verify_password, create_access_token, get_current_user
from config import settings
from security import generate_csrf_token, TokenManager
from services import AuthService

router = APIRouter()


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: UserRole = UserRole.donor


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    role: str
    full_name: str
    user_id: str
    email: str
    hospital_registered: bool | None = None
    hospital_verified: bool | None = None
    hospital_profile_complete: bool | None = None
    recipient_verified: bool | None = None
    recipient_registered: bool | None = None


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None
    role: str
    is_active: bool

    class Config:
        from_attributes = True


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    # Prevent public registration for admin accounts
    if payload.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration for admin accounts is not allowed.",
        )

    # Check duplicate email
    result = await db.execute(select(User).where(User.email == payload.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name,
        role=payload.role,
    )
    db.add(user)
    await db.flush()

    # Create role profile placeholders so missing values can be completed later.
    if payload.role == UserRole.recipient:
        db.add(Recipient(user_id=user.id, status="pending"))
    elif payload.role == UserRole.hospital:
        db.add(Hospital(user_id=user.id, is_verified=False))

    # Audit log
    db.add(AuditLog(user_id=user.id, action="USER_REGISTERED", details={"email": payload.email}))
    await db.commit()

    return {"message": "User registered successfully", "user_id": str(user.id)}


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)

    try:
        auth_data = await service.authenticate_user(
            email=form_data.username,
            password=form_data.password,
            ip_address=request.client.host if request.client else "",
            user_agent=request.headers.get("User-Agent", ""),
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Set refresh token cookie (HttpOnly, Secure, SameSite=None for cross-site in Codespaces)
    response.set_cookie(
        key="refresh_token",
        value=auth_data["refresh_token"],
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
        max_age=int(settings.REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60,
    )

    hospital_registered = None
    hospital_verified = None
    hospital_profile_complete = None
    recipient_verified = None
    recipient_registered = None

    role_value = auth_data["role"] if isinstance(auth_data["role"], str) else auth_data["role"].value
    if role_value == UserRole.hospital.value:
        hospital_result = await db.execute(
            select(Hospital).where(Hospital.user_id == uuid.UUID(auth_data["user_id"]))
        )
        hospital = hospital_result.scalar_one_or_none()
        hospital_registered = hospital is not None
        hospital_verified = bool(hospital.is_verified) if hospital else False
        hospital_profile_complete = bool(
            hospital
            and hospital.hospital_name
            and hospital.registration_number
            and hospital.city
            and hospital.state
        )
    elif role_value == UserRole.recipient.value:
        recipient_result = await db.execute(
            select(Recipient).where(Recipient.user_id == uuid.UUID(auth_data["user_id"]))
        )
        recipient = recipient_result.scalar_one_or_none()
        recipient_registered = recipient is not None
        recipient_verified = bool(recipient.is_verified) if recipient else False

    return LoginResponse(
        access_token=auth_data["access_token"],
        token_type="bearer",
        role=role_value,
        full_name=auth_data["full_name"] or "",
        user_id=auth_data["user_id"],
        email=auth_data["email"],
        hospital_registered=hospital_registered,
        hospital_verified=hospital_verified,
        hospital_profile_complete=hospital_profile_complete,
        recipient_verified=recipient_verified,
        recipient_registered=recipient_registered,
    )


@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        is_active=current_user.is_active,
    )


@router.get("/csrf-token")
async def get_csrf_token():
    """Generate CSRF token for form submission"""
    csrf_token = generate_csrf_token()
    return {"csrf_token": csrf_token}


@router.post("/refresh")
async def refresh_token(
    response: Response,
    refresh_token: str | None = Cookie(None),
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token cookie"""
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing")

    try:
        token_payload = TokenManager.verify_token(refresh_token, token_type="refresh")
        user_id = token_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    except HTTPException:
        raise

    service = AuthService(db)
    try:
        token_data = await service.refresh_access_token(user_id, refresh_token)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

    # Optional: rotate refresh token, keep existing for now
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        path="/",
        httponly=True,
        secure=True,
        samesite="none",
        max_age=int(settings.REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60,
    )

    db.add(AuditLog(user_id=uuid.UUID(user_id), action="TOKEN_REFRESHED"))
    await db.commit()

    return {"access_token": token_data["access_token"], "token_type": "bearer"}


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout user by revoking session"""
    service = AuthService(db)
    await service.logout(str(current_user.id))

    return {"message": "Logged out successfully"}
