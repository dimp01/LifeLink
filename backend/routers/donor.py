from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime
import uuid

from database import get_db
from models import Donor, DonorStatus, User, AuditLog
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
    organs_selected: List[str]
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None
    consent_agreed: bool


class DonorUpdate(BaseModel):
    full_name: Optional[str] = None
    age: Optional[int] = None
    blood_group: Optional[str] = None
    location: Optional[str] = None
    organs_selected: Optional[List[str]] = None
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None


class DonorCompletenessOut(BaseModel):
    completion_percent: int
    missing_fields: List[str]
    next_action: str


class DonorOut(BaseModel):
    id: str
    full_name: str
    age: int
    blood_group: str
    location: str
    organs_selected: List[str]
    medical_history: Optional[str]
    emergency_contact: Optional[str]
    consent_agreed: bool
    status: str
    review_reason: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: str

    class Config:
        from_attributes = True


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


@router.post("", status_code=201)
async def create_donor_profile(
    payload: DonorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Check if already registered
    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Donor profile already exists")

    if not payload.consent_agreed:
        raise HTTPException(status_code=400, detail="Consent agreement is required")

    full_name = _normalize_text(payload.full_name, 120)
    location = _normalize_text(payload.location, 120)
    medical_history = _normalize_text(payload.medical_history, 2000)
    emergency_contact = _normalize_text(payload.emergency_contact, 40)

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
        organs_selected=payload.organs_selected,
        medical_history=medical_history,
        emergency_contact=emergency_contact,
        consent_agreed=payload.consent_agreed,
    )
    db.add(donor)
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

    return DonorOut(
        id=str(donor.id),
        full_name=donor.full_name,
        age=donor.age,
        blood_group=donor.blood_group,
        location=donor.location,
        organs_selected=donor.organs_selected or [],
        medical_history=donor.medical_history,
        emergency_contact=donor.emergency_contact,
        consent_agreed=donor.consent_agreed,
        status=donor.status.value,
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
    result = await db.execute(select(Donor).where(Donor.user_id == current_user.id))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor profile not found")

    if payload.full_name is None and payload.age is None and payload.blood_group is None and payload.location is None and payload.organs_selected is None and payload.medical_history is None and payload.emergency_contact is None:
        raise HTTPException(status_code=400, detail="No fields provided for update")

    full_name = _normalize_text(payload.full_name, 120) if payload.full_name is not None else None
    location = _normalize_text(payload.location, 120) if payload.location is not None else None
    medical_history = _normalize_text(payload.medical_history, 2000) if payload.medical_history is not None else None
    emergency_contact = _normalize_text(payload.emergency_contact, 40) if payload.emergency_contact is not None else None

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
    if payload.organs_selected is not None and donor.organs_selected != payload.organs_selected:
        donor.organs_selected = payload.organs_selected
        changed_fields.append("organs_selected")
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
