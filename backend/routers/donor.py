from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, text
from datetime import datetime
import uuid

from database import get_db
from models import Donor, DonorStatus, User, UserRole, AuditLog, Recipient, Hospital, OrganRequest, MatchRequest
from auth import get_current_user

router = APIRouter()

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


class DonorCreate(BaseModel):
    full_name: str
    age: int
    blood_group: str
    location: str
    city: Optional[str] = None
    state: Optional[str] = None
    hospital_id: Optional[str] = None
    organs_selected: List[str]
    donation_mode: str = "general"  # general, after_death, relative
    relative_recipient_email: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None
    consent_agreed: bool


class DonorUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    location: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    hospital_id: Optional[str] = None
    organs_selected: Optional[List[str]] = None
    donation_mode: Optional[str] = None
    relative_recipient_email: Optional[str] = None
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None


class DonorCompletenessOut(BaseModel):
    completion_percent: int
    missing_fields: List[str]
    next_action: str


class VerifyEmailRequest(BaseModel):
    recipient_email: str


class VerifyEmailResponse(BaseModel):
    recipient_email: str
    recipient_id: str
    recipient_name: str
    status: str


class SubmitMatchRequestRequest(BaseModel):
    recipient_email: str
    message: Optional[str] = None


class SubmitMatchRequestResponse(BaseModel):
    status: str
    match_request_id: str
    message: str


class DonorOut(BaseModel):
    id: str
    full_name: str
    age: int
    blood_group: str
    location: str
    city: Optional[str] = None
    state: Optional[str] = None
    hospital_id: Optional[str] = None
    organs_selected: List[str]
    donation_mode: str
    relative_recipient_email: Optional[str] = None
    is_deceased: bool = False
    deceased_at: Optional[str] = None
    medical_history: Optional[str]
    emergency_contact: Optional[str]
    consent_agreed: bool
    status: str
    matched_recipient_id: Optional[str] = None
    match_status: Optional[str] = None
    matched_recipient_name: Optional[str] = None
    matched_recipient_age: Optional[int] = None
    matched_recipient_blood_group: Optional[str] = None
    matched_recipient_organs_needed: Optional[List[str]] = None
    matched_organ_type: Optional[str] = None
    review_reason: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


def _normalize_email(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip().lower()
    return normalized or None


def _normalize_text(value: Optional[str], max_len: int) -> Optional[str]:
    if value is None:
        return None
    normalized = " ".join(value.split()).strip()
    if len(normalized) > max_len:
        raise HTTPException(status_code=400, detail=f"Field exceeds max length of {max_len}")
    return normalized


def _validate_payload(
    *,
    full_name: Optional[str],
    age: Optional[int],
    blood_group: Optional[str],
    location: Optional[str],
    organs_selected: Optional[List[str]],
    require_organs: bool,
) -> None:
    if full_name is not None and (len(full_name.strip()) < 2 or len(full_name.strip()) > 120):
        raise HTTPException(status_code=400, detail="Full name must be between 2 and 120 characters")

    if age is not None and (age < 18 or age > 75):
        raise HTTPException(status_code=400, detail="Age must be between 18 and 75")

    if blood_group is not None and blood_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(status_code=400, detail="Invalid blood group")

    if location is not None and len(location.strip()) < 2:
        raise HTTPException(status_code=400, detail="Location is too short")

    if organs_selected is not None:
        if len(organs_selected) == 0:
            raise HTTPException(status_code=400, detail="Please select at least one organ")
        invalid_organs = [organ for organ in organs_selected if organ not in ALLOWED_ORGANS]
        if invalid_organs:
            raise HTTPException(status_code=400, detail=f"Invalid organs selected: {', '.join(invalid_organs)}")

    if require_organs and not organs_selected:
        raise HTTPException(status_code=400, detail="Please select at least one organ")


async def _resolve_uuid_or_none(raw_value: Optional[str], field_name: str):
    if raw_value in (None, ""):
        return None
    try:
        return uuid.UUID(str(raw_value))
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


async def _latest_review_metadata(db: AsyncSession, donor_id: str):
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.action == "DONOR_STATUS_UPDATED")
        .order_by(desc(AuditLog.timestamp))
    )
    logs = result.scalars().all()
    for log in logs:
        details = log.details or {}
        if details.get("donor_id") == donor_id:
            return details.get("reason"), log.timestamp.isoformat()
    return None, None


async def _unlink_donor_references(db: AsyncSession, donor_uuid: uuid.UUID) -> None:
    # Clear references in current table.
    await db.execute(
        text("UPDATE organ_requests SET donor_id = NULL WHERE donor_id = :donor_id"),
        {"donor_id": donor_uuid},
    )

    # Backward compatibility for legacy deployments that still have match_cases.
    table_check = await db.execute(text("SELECT to_regclass('public.match_cases') IS NOT NULL"))
    if table_check.scalar():
        await db.execute(
            text("DELETE FROM match_cases WHERE donor_id = :donor_id"),
            {"donor_id": donor_uuid},
        )


def _ensure_user_or_admin(current_user: User) -> None:
    # Only authenticated donor/admin accounts can mutate donor records.
    if current_user.role not in (UserRole.donor, UserRole.admin):
        raise HTTPException(status_code=403, detail="Only donor/admin accounts can perform this action")


def _ensure_owner_or_admin(current_user: User, donor: Donor) -> None:
    if current_user.role == UserRole.admin:
        return
    if donor.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this donor profile")


@router.post("", status_code=201)
async def create_donor_profile(
    payload: DonorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_user_or_admin(current_user)

    # Check if already registered
    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Donor profile already exists")

    if not payload.consent_agreed:
        raise HTTPException(status_code=400, detail="Consent agreement is required")

    full_name = _normalize_text(payload.full_name, 120)
    location = _normalize_text(payload.location, 120)
    city = _normalize_text(payload.city, 120)
    state = _normalize_text(payload.state, 120)
    medical_history = _normalize_text(payload.medical_history, 2000)
    emergency_contact = _normalize_text(payload.emergency_contact, 40)

    if payload.donation_mode not in {"general", "after_death", "relative"}:
        raise HTTPException(status_code=400, detail="Invalid donation mode")

    relative_recipient_email = _normalize_email(payload.relative_recipient_email)

    hospital_uuid = await _resolve_uuid_or_none(payload.hospital_id, "hospital_id")

    if hospital_uuid:
        hospital_result = await db.execute(select(Hospital).where(Hospital.id == hospital_uuid))
        if not hospital_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Selected hospital does not exist")

    if payload.donation_mode == "after_death" and not hospital_uuid:
        raise HTTPException(status_code=400, detail="Hospital selection is required for after-death donation")

    if payload.donation_mode == "relative" and not relative_recipient_email:
        raise HTTPException(status_code=400, detail="relative_recipient_email is required for relative donation")

    _validate_payload(
        full_name=full_name,
        age=payload.age,
        blood_group=payload.blood_group,
        location=location,
        organs_selected=payload.organs_selected,
        require_organs=True,
    )

    donor = Donor(
        user_id=current_user.id,
        full_name=full_name,
        age=payload.age,
        blood_group=payload.blood_group,
        location=location,
        city=city,
        state=state,
        hospital_id=hospital_uuid,
        organs_selected=payload.organs_selected,
        donation_mode=payload.donation_mode,
        relative_recipient_email=relative_recipient_email,
        medical_history=medical_history,
        emergency_contact=emergency_contact,
        consent_agreed=payload.consent_agreed,
    )
    db.add(donor)
    await db.flush()


    db.add(AuditLog(user_id=current_user.id, action="DONOR_REGISTERED"))
    await db.commit()
    await db.refresh(donor)

    return {"message": "Donor profile submitted successfully", "donor_id": str(donor.id)}


@router.get("/me", response_model=DonorOut)
async def get_my_donor_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    review_reason, reviewed_at = await _latest_review_metadata(db, str(donor.id))
    match_result = await db.execute(
        select(OrganRequest)
        .where(OrganRequest.donor_id == donor.id)
        .order_by(desc(OrganRequest.matched_date), desc(OrganRequest.request_date))
        .limit(1)
    )
    latest_match = match_result.scalar_one_or_none()
    
    # Fetch matched recipient details if exists
    matched_recipient = None
    if latest_match and latest_match.recipient_id:
        recipient_result = await db.execute(
            select(Recipient).where(Recipient.id == latest_match.recipient_id)
        )
        matched_recipient = recipient_result.scalar_one_or_none()

    return DonorOut(
        id=str(donor.id),
        full_name=donor.full_name,
        age=donor.age,
        blood_group=donor.blood_group,
        location=donor.location,
        city=donor.city,
        state=donor.state,
        hospital_id=str(donor.hospital_id) if donor.hospital_id else None,
        organs_selected=donor.organs_selected or [],
        donation_mode=donor.donation_mode or "general",
        relative_recipient_email=donor.relative_recipient_email,
        is_deceased=bool(donor.is_deceased),
        deceased_at=donor.deceased_at.isoformat() if donor.deceased_at else None,
        medical_history=donor.medical_history,
        emergency_contact=donor.emergency_contact,
        consent_agreed=donor.consent_agreed,
        status=donor.status.value,
        matched_recipient_id=str(latest_match.recipient_id) if latest_match and latest_match.recipient_id else None,
        match_status=latest_match.status if latest_match else None,
        matched_recipient_name=matched_recipient.full_name if matched_recipient else None,
        matched_recipient_age=matched_recipient.age if matched_recipient else None,
        matched_recipient_blood_group=matched_recipient.blood_group if matched_recipient else None,
        matched_recipient_organs_needed=matched_recipient.organ_needed if matched_recipient else None,
        matched_organ_type=latest_match.organ_type if latest_match else None,
        review_reason=review_reason,
        reviewed_at=reviewed_at,
        created_at=donor.created_at.isoformat(),
    )


@router.patch("/me")
async def update_donor_profile(
    payload: DonorUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_user_or_admin(current_user)

    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    if (
        payload.full_name is None
        and payload.age is None
        and payload.blood_group is None
        and payload.location is None
        and payload.city is None
        and payload.state is None
        and payload.hospital_id is None
        and payload.organs_selected is None
        and payload.donation_mode is None
        and payload.relative_recipient_email is None
        and payload.medical_history is None
        and payload.emergency_contact is None
    ):
        raise HTTPException(status_code=400, detail="No fields provided for update")

    full_name = _normalize_text(payload.full_name, 120) if payload.full_name is not None else None
    location = _normalize_text(payload.location, 120) if payload.location is not None else None
    city = _normalize_text(payload.city, 120) if payload.city is not None else None
    state = _normalize_text(payload.state, 120) if payload.state is not None else None
    medical_history = _normalize_text(payload.medical_history, 2000) if payload.medical_history is not None else None
    emergency_contact = _normalize_text(payload.emergency_contact, 40) if payload.emergency_contact is not None else None

    donation_mode = payload.donation_mode if payload.donation_mode is not None else donor.donation_mode
    if donation_mode not in {"general", "after_death", "relative"}:
        raise HTTPException(status_code=400, detail="Invalid donation mode")

    hospital_uuid = await _resolve_uuid_or_none(payload.hospital_id, "hospital_id") if payload.hospital_id is not None else donor.hospital_id

    if hospital_uuid:
        hospital_result = await db.execute(select(Hospital).where(Hospital.id == hospital_uuid))
        if not hospital_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Selected hospital does not exist")

    if donation_mode == "after_death" and not hospital_uuid:
        raise HTTPException(status_code=400, detail="Hospital selection is required for after-death donation")

    relative_recipient_email = _normalize_email(payload.relative_recipient_email) if payload.relative_recipient_email is not None else donor.relative_recipient_email
    if donation_mode == "relative" and not relative_recipient_email:
        raise HTTPException(status_code=400, detail="relative_recipient_email is required for relative donation")

    _validate_payload(
        full_name=full_name,
        age=payload.age,
        blood_group=payload.blood_group,
        location=location,
        organs_selected=payload.organs_selected,
        require_organs=False,
    )

    changed_fields = []

    if full_name is not None and donor.full_name != full_name:
        donor.full_name = full_name
        changed_fields.append("full_name")
    if payload.age is not None and donor.age != payload.age:
        donor.age = payload.age
        changed_fields.append("age")
    if payload.blood_group is not None and donor.blood_group != payload.blood_group:
        donor.blood_group = payload.blood_group
        changed_fields.append("blood_group")
    if location is not None and donor.location != location:
        donor.location = location
        changed_fields.append("location")
    if city is not None and donor.city != city:
        donor.city = city
        changed_fields.append("city")
    if state is not None and donor.state != state:
        donor.state = state
        changed_fields.append("state")
    if payload.hospital_id is not None and donor.hospital_id != hospital_uuid:
        donor.hospital_id = hospital_uuid
        changed_fields.append("hospital_id")
    if payload.organs_selected is not None and donor.organs_selected != payload.organs_selected:
        donor.organs_selected = payload.organs_selected
        changed_fields.append("organs_selected")
    if payload.donation_mode is not None and donor.donation_mode != donation_mode:
        donor.donation_mode = donation_mode
        changed_fields.append("donation_mode")
    if payload.relative_recipient_email is not None and donor.relative_recipient_email != relative_recipient_email:
        donor.relative_recipient_email = relative_recipient_email
        changed_fields.append("relative_recipient_email")
    if payload.medical_history is not None and donor.medical_history != medical_history:
        donor.medical_history = medical_history
        changed_fields.append("medical_history")
    if payload.emergency_contact is not None and donor.emergency_contact != emergency_contact:
        donor.emergency_contact = emergency_contact
        changed_fields.append("emergency_contact")

    donor.updated_at = datetime.utcnow()

    db.add(
        AuditLog(
            user_id=current_user.id,
            action="DONOR_UPDATED",
            details={"changed_fields": changed_fields},
        )
    )
    await db.commit()

    return {"message": "Donor profile updated successfully", "changed_fields": changed_fields}


@router.delete("/me")
async def delete_my_donor_profile(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_user_or_admin(current_user)

    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    donor_id = str(donor.id)
    await _unlink_donor_references(db, donor.id)
    await db.delete(donor)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="DONOR_DELETED",
            details={"donor_id": donor_id, "scope": "self"},
        )
    )
    await db.commit()

    return {"message": "Donor profile deleted successfully"}


@router.delete("/{donor_id}")
async def delete_donor_profile(
    donor_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _ensure_user_or_admin(current_user)

    try:
        donor_uuid = uuid.UUID(donor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid donor ID")

    result = await db.execute(select(Donor).where(Donor.id == donor_uuid))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    _ensure_owner_or_admin(current_user, donor)

    await _unlink_donor_references(db, donor.id)
    await db.delete(donor)
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="DONOR_DELETED",
            details={"donor_id": donor_id, "scope": "admin_or_owner"},
        )
    )
    await db.commit()

    return {"message": "Donor profile deleted successfully"}


@router.put("/update")
async def update_donor_profile_legacy(
    payload: DonorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Backward-compatible update endpoint for older clients."""
    return await update_donor_profile(
        payload=DonorUpdate(
            full_name=payload.full_name,
            age=payload.age,
            blood_group=payload.blood_group,
            location=payload.location,
            organs_selected=payload.organs_selected,
            donation_mode=payload.donation_mode,
            relative_recipient_email=payload.relative_recipient_email,
            medical_history=payload.medical_history,
            emergency_contact=payload.emergency_contact,
        ),
        db=db,
        current_user=current_user,
    )


@router.get("/me/completeness", response_model=DonorCompletenessOut)
async def get_donor_profile_completeness(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    checks = {
        "full_name": bool(donor.full_name),
        "age": donor.age is not None,
        "blood_group": bool(donor.blood_group),
        "location": bool(donor.location),
        "organs_selected": bool(donor.organs_selected),
        "emergency_contact": bool((donor.emergency_contact or "").strip()),
        "medical_history": bool((donor.medical_history or "").strip()),
        "consent_agreed": donor.consent_agreed is True,
    }

    completed = sum(1 for value in checks.values() if value)
    total = len(checks)
    missing_fields = [field for field, value in checks.items() if not value]
    completion_percent = int(round((completed / total) * 100)) if total else 0

    if completion_percent == 100:
        next_action = "Profile complete. Wait for review updates from admin."
    elif donor.status == DonorStatus.rejected:
        next_action = "Review the rejection note and update your profile details."
    else:
        next_action = "Complete missing profile details to speed up verification."

    return DonorCompletenessOut(
        completion_percent=completion_percent,
        missing_fields=missing_fields,
        next_action=next_action,
    )


@router.post("/verify-email", response_model=VerifyEmailResponse)
async def verify_recipient_email(
    payload: VerifyEmailRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Verify that a recipient email exists before submitting a relative donation request."""
    if current_user.role != UserRole.donor:
        raise HTTPException(status_code=403, detail="Only donors can verify recipient emails")

    normalized_email = _normalize_email(payload.recipient_email)
    if not normalized_email:
        raise HTTPException(status_code=400, detail="recipient_email is required")

    recipient_user_result = await db.execute(select(User).where(User.email == normalized_email))
    recipient_user = recipient_user_result.scalar_one_or_none()
    if not recipient_user:
        raise HTTPException(status_code=404, detail="Recipient email not found in system")
    if recipient_user.role != UserRole.recipient:
        raise HTTPException(status_code=400, detail="Email does not belong to a recipient account")
    if not recipient_user.is_active:
        raise HTTPException(status_code=400, detail="Recipient account is inactive")

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == recipient_user.id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient profile not found")
    if not recipient.is_verified:
        raise HTTPException(status_code=400, detail="Recipient has not completed verification yet")

    return VerifyEmailResponse(
        recipient_email=normalized_email,
        recipient_id=str(recipient.id),
        recipient_name=recipient.full_name or "Unknown",
        status="verified",
    )


@router.post("/submit-relative-request", response_model=SubmitMatchRequestResponse)
async def submit_relative_match_request(
    payload: SubmitMatchRequestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit a match request to a relative recipient."""
    if current_user.role != UserRole.donor:
        raise HTTPException(status_code=403, detail="Only donors can submit match requests")

    donor_result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")
    if donor.donation_mode != "relative":
        raise HTTPException(status_code=400, detail="Match requests only for relative donation mode")

    normalized_email = _normalize_email(payload.recipient_email)
    if not normalized_email:
        raise HTTPException(status_code=400, detail="recipient_email is required")

    recipient_user_result = await db.execute(select(User).where(User.email == normalized_email))
    recipient_user = recipient_user_result.scalar_one_or_none()
    if not recipient_user or recipient_user.role != UserRole.recipient:
        raise HTTPException(status_code=404, detail="Recipient email not found in system")
    if not recipient_user.is_active:
        raise HTTPException(status_code=400, detail="Recipient account is inactive")

    recipient_result = await db.execute(select(Recipient).where(Recipient.user_id == recipient_user.id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient profile not found")
    if not recipient.is_verified:
        raise HTTPException(status_code=400, detail="Recipient has not completed verification yet")

    duplicate_result = await db.execute(
        select(MatchRequest)
        .where(MatchRequest.donor_id == donor.id)
        .where(MatchRequest.recipient_id == recipient.id)
        .where(MatchRequest.status == "pending")
    )
    duplicate_pending = duplicate_result.scalar_one_or_none()
    if duplicate_pending:
        raise HTTPException(status_code=400, detail="A pending match request already exists for this recipient")

    donor.relative_recipient_email = normalized_email
    donor.updated_at = datetime.utcnow()

    match_request = MatchRequest(
        donor_id=donor.id,
        recipient_id=recipient.id,
        status="pending",
        message=payload.message or "",
        requested_at=datetime.utcnow(),
    )
    db.add(match_request)
    await db.flush()
    await db.commit()

    return SubmitMatchRequestResponse(
        status="pending",
        match_request_id=str(match_request.id),
        message="Match request submitted successfully. Recipient will review and respond.",
    )
