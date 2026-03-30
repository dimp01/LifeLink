"""
Recipient verification routes
Handles recipient verification form submissions and status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from pydantic import BaseModel
from sqlalchemy import select, desc
from datetime import datetime
import uuid

class MatchRequestOut(BaseModel):
    id: str
    donor_id: str
    donor_name: str
    donor_blood_group: str
    donor_organs: List[str]
    message: Optional[str] = None
    status: str
    requested_at: str


class MatchRequestResponse(BaseModel):
    status: str
    message: str


from database import get_db
from auth import get_current_user
from services import RecipientService
from models import User, RecipientVerification, Recipient, Hospital, OrganRequest, MatchRequest, Donor

router = APIRouter(prefix="/recipient", tags=["recipient"])


@router.get("/verification")
async def get_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current verification record for user"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    # Prefer Recipient profile state because admin approval/rejection is persisted there.
    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = recipient_result.scalar_one_or_none()

    if recipient:
        normalized_status = (recipient.status or "not_started").lower()
        inferred_verified = normalized_status in {"verified", "approved", "matched", "completed"}
        is_verified = bool(recipient.is_verified or inferred_verified)

        return {
            "id": str(recipient.id),
            "status": "verified" if is_verified else normalized_status,
            "current_step": 5 if is_verified else (1 if normalized_status != "not_started" else 0),
            "submitted_at": recipient.submitted_at.isoformat() if recipient.submitted_at else None,
            "verified_at": recipient.verified_at.isoformat() if recipient.verified_at else None,
            "is_verified": is_verified,
            "created_at": recipient.created_at.isoformat(),
            "updated_at": recipient.updated_at.isoformat(),
        }

    service = RecipientService(db)
    verification = await service.get_verification(str(current_user.id))

    if not verification:
        return {
            "status": "not_started",
            "current_step": 0,
            "data": None,
        }

    return {
        "id": str(verification.id),
        "status": verification.status,
        "current_step": verification.current_step,
        "submitted_at": verification.submitted_at.isoformat() if verification.submitted_at else None,
        "created_at": verification.created_at.isoformat(),
        "updated_at": verification.updated_at.isoformat(),
    }


@router.post("/verification/start")
async def start_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or retrieve verification record"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    service = RecipientService(db)
    verification = await service.get_verification(str(current_user.id))

    if not verification:
        verification = await service.create_verification(str(current_user.id))

    return {
        "id": str(verification.id),
        "status": verification.status,
        "message": "Verification process started",
    }


@router.post("/verification/step/{step_number}")
async def save_step(
    step_number: int,
    data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Save form data for specific step (1-5)"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    if step_number < 1 or step_number > 5:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Step number must be between 1 and 5",
        )

    try:
        service = RecipientService(db)
        verification = await service.save_step_data(
            user_id=str(current_user.id),
            step=step_number,
            data=data,
        )

        return {
            "id": str(verification.id),
            "status": verification.status,
            "current_step": verification.current_step,
            "message": f"Step {step_number} saved successfully",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/verification/submit")
async def submit_verification(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit completed verification for review"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    try:
        service = RecipientService(db)
        verification = await service.submit_verification(str(current_user.id))

        return {
            "id": str(verification.id),
            "status": verification.status,
            "submitted_at": verification.submitted_at.isoformat(),
            "message": "Verification submitted successfully for review",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/verification/summary")
async def get_verification_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get complete verification form data as summary"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    service = RecipientService(db)
    summary = await service.get_verification_summary(str(current_user.id))

    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No verification record found",
        )

    return summary


# ============ Recipient Profile Management ============

ALLOWED_BLOOD_GROUPS = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
ALLOWED_ORGANS = {
    "Kidney",
    "Liver",
    "Heart",
    "Lungs",
    "Eyes",
    "Cornea",
    "Pancreas",
    "Intestine",
    "Skin",
    "Bone Marrow",
}


class RecipientProfileCreate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    medical_condition: Optional[str] = None
    organ_needed: Optional[List[str]] = None
    urgency: Optional[str] = "standard"
    hospital_id: Optional[str] = None


class RecipientProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    medical_condition: Optional[str] = None
    organ_needed: Optional[List[str]] = None
    urgency: Optional[str] = None
    hospital_id: Optional[str] = None


class RecipientProfileOut(BaseModel):
    id: str
    full_name: Optional[str]
    age: Optional[int]
    blood_group: Optional[str]
    medical_condition: Optional[str]
    organ_needed: Optional[List[str]]
    urgency: Optional[str]
    status: str
    hospital_id: Optional[str]
    hospital_name: Optional[str]
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def validate_recipient_profile(payload) -> None:
    """Validate recipient profile data"""
    if hasattr(payload, "full_name") and payload.full_name is not None:
        if len(payload.full_name.strip()) < 2 or len(payload.full_name.strip()) > 120:
            raise HTTPException(status_code=400, detail="Full name must be between 2 and 120 characters")

    if hasattr(payload, "age") and payload.age is not None:
        if payload.age < 10 or payload.age > 100:
            raise HTTPException(status_code=400, detail="Age must be between 10 and 100")

    if hasattr(payload, "blood_group") and payload.blood_group is not None:
        if payload.blood_group not in ALLOWED_BLOOD_GROUPS:
            raise HTTPException(status_code=400, detail="Invalid blood group")

    if hasattr(payload, "organ_needed") and payload.organ_needed is not None:
        if len(payload.organ_needed) == 0:
            raise HTTPException(status_code=400, detail="Please select at least one organ")
        invalid_organs = [organ for organ in payload.organ_needed if organ not in ALLOWED_ORGANS]
        if invalid_organs:
            raise HTTPException(status_code=400, detail=f"Invalid organs: {', '.join(invalid_organs)}")

    if hasattr(payload, "urgency") and payload.urgency is not None:
        if payload.urgency not in ["urgent", "high", "standard"]:
            raise HTTPException(status_code=400, detail="Invalid urgency level")


@router.post("/profile", status_code=status.HTTP_201_CREATED, response_model=RecipientProfileOut)
async def create_recipient_profile(
    payload: RecipientProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or complete recipient profile"""
    if current_user.role not in ["recipient", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can create profiles",
        )

    # If placeholder exists, complete/update it.
    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    validate_recipient_profile(payload)

    if recipient:
        if payload.full_name is not None:
            recipient.full_name = payload.full_name.strip()
        if payload.age is not None:
            recipient.age = payload.age
        if payload.blood_group is not None:
            recipient.blood_group = payload.blood_group
        if payload.medical_condition is not None:
            recipient.medical_condition = payload.medical_condition.strip()
        if payload.organ_needed is not None:
            recipient.organ_needed = payload.organ_needed
        if payload.urgency is not None:
            recipient.urgency = payload.urgency
        if payload.hospital_id is not None:
            try:
                recipient.hospital_id = uuid.UUID(payload.hospital_id) if payload.hospital_id else None
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid hospital_id")
        recipient.updated_at = datetime.utcnow()
        await db.flush()
    else:
        recipient = Recipient(
            user_id=current_user.id,
            full_name=payload.full_name.strip() if payload.full_name else None,
            age=payload.age,
            blood_group=payload.blood_group,
            medical_condition=payload.medical_condition.strip() if payload.medical_condition else None,
            organ_needed=payload.organ_needed,
            urgency=payload.urgency,
            hospital_id=uuid.UUID(payload.hospital_id) if payload.hospital_id else None,
        )
        db.add(recipient)
        await db.flush()

    return RecipientProfileOut(
        id=str(recipient.id),
        full_name=recipient.full_name,
        age=recipient.age,
        blood_group=recipient.blood_group,
        medical_condition=recipient.medical_condition,
        organ_needed=recipient.organ_needed,
        urgency=recipient.urgency,
        status=recipient.status,
        hospital_id=str(recipient.hospital_id) if recipient.hospital_id else None,
        hospital_name=None,
        created_at=recipient.created_at.isoformat(),
        updated_at=recipient.updated_at.isoformat(),
    )


@router.get("/profile", response_model=RecipientProfileOut)
async def get_recipient_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current recipient profile"""
    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient profile not found")

    hospital_name = None
    if recipient.hospital_id:
        hospital_result = await db.execute(select(Hospital).where(Hospital.id == recipient.hospital_id))
        hospital = hospital_result.scalar_one_or_none()
        if hospital:
            hospital_name = hospital.hospital_name

    return RecipientProfileOut(
        id=str(recipient.id),
        full_name=recipient.full_name,
        age=recipient.age,
        blood_group=recipient.blood_group,
        medical_condition=recipient.medical_condition,
        organ_needed=recipient.organ_needed,
        urgency=recipient.urgency,
        status=recipient.status,
        hospital_id=str(recipient.hospital_id) if recipient.hospital_id else None,
        hospital_name=hospital_name,
        created_at=recipient.created_at.isoformat(),
        updated_at=recipient.updated_at.isoformat(),
    )


@router.put("/profile", response_model=RecipientProfileOut)
async def update_recipient_profile(
    payload: RecipientProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update recipient profile"""
    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient profile not found")

    validate_recipient_profile(payload)

    if payload.full_name is not None:
        recipient.full_name = payload.full_name.strip()
    if payload.age is not None:
        recipient.age = payload.age
    if payload.blood_group is not None:
        recipient.blood_group = payload.blood_group
    if payload.medical_condition is not None:
        recipient.medical_condition = payload.medical_condition.strip()
    if payload.organ_needed is not None:
        recipient.organ_needed = payload.organ_needed
    if payload.urgency is not None:
        recipient.urgency = payload.urgency
    if payload.hospital_id is not None:
        try:
            recipient.hospital_id = uuid.UUID(payload.hospital_id) if payload.hospital_id else None
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hospital_id")

    recipient.updated_at = datetime.utcnow()
    await db.flush()

    hospital_name = None
    if recipient.hospital_id:
        hospital_result = await db.execute(select(Hospital).where(Hospital.id == recipient.hospital_id))
        hospital = hospital_result.scalar_one_or_none()
        if hospital:
            hospital_name = hospital.hospital_name

    return RecipientProfileOut(
        id=str(recipient.id),
        full_name=recipient.full_name,
        age=recipient.age,
        blood_group=recipient.blood_group,
        medical_condition=recipient.medical_condition,
        organ_needed=recipient.organ_needed,
        urgency=recipient.urgency,
        status=recipient.status,
        hospital_id=str(recipient.hospital_id) if recipient.hospital_id else None,
        hospital_name=hospital_name,
        created_at=recipient.created_at.isoformat(),
        updated_at=recipient.updated_at.isoformat(),
    )


@router.get("/profile/status")
async def get_recipient_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recipient status and application progress"""
    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient profile not found")

    # Get associated organ requests
    requests_result = await db.execute(
        select(OrganRequest).where(OrganRequest.recipient_id == recipient.id)
    )
    requests = requests_result.scalars().all()

    return {
        "recipient_id": str(recipient.id),
        "status": recipient.status,
        "organ_needed": recipient.organ_needed,
        "urgency": recipient.urgency,
        "pending_requests": len([r for r in requests if r.status == "pending"]),
        "matched_requests": len([r for r in requests if r.status == "matched"]),
        "completed_requests": len([r for r in requests if r.status == "completed"]),
        "created_at": recipient.created_at.isoformat(),
        "updated_at": recipient.updated_at.isoformat(),
    }


# ============ Recipient Registration and Verification ============

class RecipientRegistrationRequest(BaseModel):
    """Registration form data for recipient verification"""
    full_name: str
    age: int
    blood_group: str
    phone: str
    address: str
    medical_condition: str
    organ_needed: List[str]
    urgency: str = "standard"
    hospital_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    hospital_contact_name: Optional[str] = None
    verification_notes: Optional[str] = None
    documents: Optional[List[dict]] = None  # List of document metadata


class RecipientVerificationStatus(BaseModel):
    """Recipient verification status response"""
    recipient_id: str
    is_verified: bool
    status: str
    submitted_at: Optional[str] = None
    verified_at: Optional[str] = None
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    organ_needed: Optional[List[str]] = None
    urgency: Optional[str] = None
    documents: Optional[dict] = None
    verification_notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class RecipientReviewRequest(BaseModel):
    reviewer_notes: Optional[str] = None


class RecipientRejectRequest(BaseModel):
    reviewer_notes: str


class RecipientDeactivateRequest(BaseModel):
    reason: Optional[str] = None


@router.post("/register")
async def register_recipient(
    payload: RecipientRegistrationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register/submit recipient for verification"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can register",
        )

    # Validate input
    validate_recipient_profile(payload)
    
    if not payload.phone or len(payload.phone) < 10:
        raise HTTPException(status_code=400, detail="Valid phone number required")
    
    if not payload.address or len(payload.address) < 5:
        raise HTTPException(status_code=400, detail="Address must be at least 5 characters")

    # Check if recipient already exists
    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    if recipient:
        # Update existing recipient
        recipient.full_name = payload.full_name.strip()
        recipient.age = payload.age
        recipient.blood_group = payload.blood_group
        recipient.phone = payload.phone.strip()
        recipient.address = payload.address.strip()
        recipient.medical_condition = payload.medical_condition.strip()
        recipient.organ_needed = payload.organ_needed
        recipient.urgency = payload.urgency
        if payload.hospital_id:
            try:
                recipient.hospital_id = uuid.UUID(payload.hospital_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid hospital_id")
        recipient.hospital_contact_name = payload.hospital_contact_name
        recipient.verification_notes = payload.verification_notes
        recipient.documents = payload.documents or []
        recipient.submitted_at = datetime.utcnow()
        recipient.status = "pending"  # Mark as pending review
    else:
        # Create new recipient
        recipient = Recipient(
            user_id=current_user.id,
            full_name=payload.full_name.strip(),
            age=payload.age,
            blood_group=payload.blood_group,
            phone=payload.phone.strip(),
            address=(f"{(payload.address or '').strip()} | {(payload.city or '').strip()}, {(payload.state or '').strip()}").strip(" |,"),
            medical_condition=payload.medical_condition.strip(),
            organ_needed=payload.organ_needed,
            urgency=payload.urgency,
            hospital_id=uuid.UUID(payload.hospital_id) if payload.hospital_id else None,
            hospital_contact_name=payload.hospital_contact_name,
            verification_notes=payload.verification_notes,
            documents=payload.documents or [],
            submitted_at=datetime.utcnow(),
            status="pending",
        )
        db.add(recipient)

    await db.flush()
    await db.commit()

    return {
        "id": str(recipient.id),
        "user_id": str(recipient.user_id),
        "status": recipient.status,
        "submitted_at": recipient.submitted_at.isoformat() if recipient.submitted_at else None,
        "message": "Recipient registration submitted successfully. Please wait for admin verification.",
    }


@router.get("/me/verification")
async def get_recipient_verification_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recipient's own verification status"""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        return {
            "recipient_id": None,
            "is_verified": False,
            "status": "not_started",
            "submitted_at": None,
            "verified_at": None,
            "full_name": current_user.full_name,
            "documents": [],
        }

    normalized_status = (recipient.status or "not_started").lower()
    inferred_verified = normalized_status in {"verified", "approved", "matched", "completed"}
    match_result = await db.execute(
        select(OrganRequest)
        .where(OrganRequest.recipient_id == recipient.id)
        .order_by(desc(OrganRequest.matched_date), desc(OrganRequest.request_date))
        .limit(1)
    )
    latest_match = match_result.scalar_one_or_none()

    return {
        "recipient_id": str(recipient.id),
        "is_verified": bool(recipient.is_verified or inferred_verified),
        "status": "verified" if (recipient.is_verified or inferred_verified) else normalized_status,
        "user_is_active": bool(current_user.is_active),
        "profile_is_active": normalized_status not in {"inactive", "cancelled"},
        "submitted_at": recipient.submitted_at.isoformat() if recipient.submitted_at else None,
        "verified_at": recipient.verified_at.isoformat() if recipient.verified_at else None,
        "full_name": recipient.full_name,
        "age": recipient.age,
        "blood_group": recipient.blood_group,
        "phone": recipient.phone,
        "address": recipient.address,
        "medical_condition": recipient.medical_condition,
        "organ_needed": recipient.organ_needed,
        "urgency": recipient.urgency,
        "documents": recipient.documents or [],
        "verification_notes": recipient.verification_notes,
        "reviewer_notes": recipient.reviewer_notes,
        "active_match": {
            "donor_id": str(latest_match.donor_id) if latest_match and latest_match.donor_id else None,
            "status": latest_match.status,
            "organ_type": latest_match.organ_type,
            "matched_date": latest_match.matched_date.isoformat() if latest_match and latest_match.matched_date else None,
        } if latest_match else None,
    }


@router.post("/deactivate")
async def deactivate_recipient(
    payload: RecipientDeactivateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel recipient verification/need and deactivate account + profile."""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    reason = (payload.reason or "Recipient requested deactivation").strip()

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = recipient_result.scalar_one_or_none()

    if recipient:
        recipient.status = "inactive"
        recipient.is_verified = False
        existing_notes = (recipient.verification_notes or "").strip()
        recipient.verification_notes = (
            f"{existing_notes}\n[Recipient Deactivated] {reason}" if existing_notes else f"[Recipient Deactivated] {reason}"
        )
        recipient.updated_at = datetime.utcnow()

    verification_result = await db.execute(
        select(RecipientVerification).where(RecipientVerification.user_id == current_user.id)
    )
    verification = verification_result.scalar_one_or_none()
    if verification:
        verification.status = "cancelled"
        verification.updated_at = datetime.utcnow()

    current_user.is_active = False

    await db.flush()
    await db.commit()

    return {
        "message": "Recipient verification/request cancelled and account deactivated.",
        "user_is_active": False,
        "profile_status": "inactive",
    }


# ============ Admin Endpoints ============

@router.get("/admin/pending")
async def get_pending_recipients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending recipient verifications (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    result = await db.execute(
        select(Recipient).where(Recipient.status == "pending").order_by(desc(Recipient.submitted_at))
    )
    recipients = result.scalars().all()

    return [
        {
            "recipient_id": str(r.id),
            "user_id": str(r.user_id),
            "full_name": r.full_name,
            "age": r.age,
            "blood_group": r.blood_group,
            "organ_needed": r.organ_needed,
            "urgency": r.urgency,
            "medical_condition": r.medical_condition,
            "phone": r.phone,
            "address": r.address,
            "hospital_contact_name": r.hospital_contact_name,
            "documents": r.documents or [],
            "verification_notes": r.verification_notes,
            "submitted_at": r.submitted_at.isoformat() if r.submitted_at else None,
            "created_at": r.created_at.isoformat(),
        }
        for r in recipients
    ]


@router.get("/admin/{recipient_id}")
async def get_recipient_for_admin(
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed recipient information for admin review"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can access this endpoint",
        )

    result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    # Get user details for contact info
    user_result = await db.execute(select(User).where(User.id == recipient.user_id))
    user = user_result.scalar_one_or_none()

    return {
        "recipient_id": str(recipient.id),
        "user_id": str(recipient.user_id),
        "user_email": user.email if user else None,
        "full_name": recipient.full_name,
        "age": recipient.age,
        "blood_group": recipient.blood_group,
        "phone": recipient.phone,
        "address": recipient.address,
        "medical_condition": recipient.medical_condition,
        "organ_needed": recipient.organ_needed,
        "urgency": recipient.urgency,
        "hospital_contact_name": recipient.hospital_contact_name,
        "status": recipient.status,
        "is_verified": recipient.is_verified,
        "documents": recipient.documents or [],
        "verification_notes": recipient.verification_notes,
        "reviewer_notes": recipient.reviewer_notes,
        "submitted_at": recipient.submitted_at.isoformat() if recipient.submitted_at else None,
        "verified_at": recipient.verified_at.isoformat() if recipient.verified_at else None,
        "created_at": recipient.created_at.isoformat(),
        "updated_at": recipient.updated_at.isoformat(),
    }


@router.post("/admin/{recipient_id}/approve")
async def approve_recipient(
    recipient_id: str,
    payload: RecipientReviewRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Approve recipient verification (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can approve recipients",
        )

    result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.is_verified = True
    recipient.status = "verified"
    recipient.verified_at = datetime.utcnow()
    recipient.verified_by = current_user.id
    recipient.reviewer_notes = payload.reviewer_notes
    recipient.updated_at = datetime.utcnow()

    await db.flush()
    await db.commit()

    return {
        "recipient_id": str(recipient.id),
        "status": recipient.status,
        "is_verified": recipient.is_verified,
        "verified_at": recipient.verified_at.isoformat(),
        "message": "Recipient approved successfully",
    }


@router.post("/admin/{recipient_id}/reject")
async def reject_recipient(
    recipient_id: str,
    payload: RecipientRejectRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject recipient verification (admin only)"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can reject recipients",
        )

    if not payload.reviewer_notes or len(payload.reviewer_notes.strip()) < 5:
        raise HTTPException(status_code=400, detail="Rejection notes must be at least 5 characters")

    result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.status = "rejected"
    recipient.verified_at = datetime.utcnow()
    recipient.verified_by = current_user.id
    recipient.reviewer_notes = payload.reviewer_notes
    recipient.updated_at = datetime.utcnow()

    await db.flush()
    await db.commit()

    return {
        "recipient_id": str(recipient.id),
        "status": recipient.status,
        "verified_at": recipient.verified_at.isoformat(),
        "message": "Recipient rejected. Reviewer notes have been recorded.",
    }

@router.get("/match-requests", response_model=List[MatchRequestOut])
async def get_recipient_match_requests(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all pending match requests for the current recipient."""
    if current_user.role != "recipient":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only recipients can access this endpoint",
        )

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient profile not found")

    requests_result = await db.execute(
        select(MatchRequest)
        .where(MatchRequest.recipient_id == recipient.id)
        .where(MatchRequest.status == "pending")
        .order_by(desc(MatchRequest.requested_at))
    )
    match_requests = requests_result.scalars().all()

    result = []
    for mr in match_requests:
        donor_result = await db.execute(select(Donor).where(Donor.id == mr.donor_id))
        donor = donor_result.scalar_one_or_none()
        if donor:
            result.append(
                MatchRequestOut(
                    id=str(mr.id),
                    donor_id=str(donor.id),
                    donor_name=donor.full_name,
                    donor_blood_group=donor.blood_group,
                    donor_organs=donor.organs_selected or [],
                    message=mr.message,
                    status=mr.status,
                    requested_at=mr.requested_at.isoformat() if mr.requested_at else "",
                )
            )

    return result


@router.post("/match-requests/{request_id}/accept", response_model=MatchRequestResponse)
async def accept_match_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept a match request and inactivate both donor and recipient accounts."""
    if current_user.role != "recipient":
        raise HTTPException(status_code=403, detail="Only recipients can accept match requests")

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient profile not found")

    match_request_result = await db.execute(select(MatchRequest).where(MatchRequest.id == request_uuid))
    match_request = match_request_result.scalar_one_or_none()
    if not match_request:
        raise HTTPException(status_code=404, detail="Match request not found")

    if match_request.recipient_id != recipient.id:
        raise HTTPException(status_code=403, detail="This request is not for you")
    if match_request.status != "pending":
        raise HTTPException(status_code=400, detail="Match request can no longer be accepted")

    match_request.status = "accepted"
    match_request.responded_at = datetime.utcnow()

    donor_result = await db.execute(select(Donor).where(Donor.id == match_request.donor_id))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    donor_user_result = await db.execute(select(User).where(User.id == donor.user_id))
    donor_user = donor_user_result.scalar_one_or_none()
    if donor_user:
        donor_user.is_active = False
    current_user.is_active = False

    recipient.status = "inactive"
    recipient.updated_at = datetime.utcnow()
    donor.updated_at = datetime.utcnow()

    organ_type = (donor.organs_selected or ["Unknown"])[0]
    db.add(
        OrganRequest(
            donor_id=donor.id,
            recipient_id=recipient.id,
            organ_type=organ_type,
            status="matched",
            match_compatibility=1.0,
            matched_date=datetime.utcnow(),
            notes="Match accepted through relative donation request",
        )
    )

    await db.flush()
    await db.commit()

    return MatchRequestResponse(
        status="accepted",
        message="Match request accepted. Both accounts are now inactive.",
    )


@router.post("/match-requests/{request_id}/reject", response_model=MatchRequestResponse)
async def reject_match_request(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Reject a match request."""
    if current_user.role != "recipient":
        raise HTTPException(status_code=403, detail="Only recipients can reject match requests")

    try:
        request_uuid = uuid.UUID(request_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid request ID")

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == current_user.id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient profile not found")

    match_request_result = await db.execute(select(MatchRequest).where(MatchRequest.id == request_uuid))
    match_request = match_request_result.scalar_one_or_none()
    if not match_request:
        raise HTTPException(status_code=404, detail="Match request not found")

    if match_request.recipient_id != recipient.id:
        raise HTTPException(status_code=403, detail="This request is not for you")
    if match_request.status != "pending":
        raise HTTPException(status_code=400, detail="Match request can no longer be rejected")

    match_request.status = "rejected"
    match_request.responded_at = datetime.utcnow()

    await db.flush()
    await db.commit()

    return MatchRequestResponse(status="rejected", message="Match request rejected successfully.")

