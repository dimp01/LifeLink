from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, or_, case
from datetime import datetime
import uuid

from database import get_db
from models import Hospital, User, UserRole, Recipient, OrganRequest, Donor, DonorStatus
from auth import get_current_user

router = APIRouter(prefix="/hospital", tags=["Hospital"])


class HospitalCreate(BaseModel):
    hospital_name: Optional[str] = None
    registration_number: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
    bed_capacity: Optional[int] = None
    specializations: Optional[List[str]] = None


class HospitalUpdate(BaseModel):
    hospital_name: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    bed_capacity: Optional[int] = None
    specializations: Optional[List[str]] = None


class HospitalOut(BaseModel):
    id: str
    hospital_name: Optional[str]
    registration_number: Optional[str]
    city: Optional[str]
    state: Optional[str]
    phone: Optional[str]
    email: Optional[str]
    website: Optional[str]
    bed_capacity: Optional[int]
    specializations: Optional[List[str]]
    is_verified: Optional[bool]
    created_at: str

    class Config:
        from_attributes = True


class RecipientOut(BaseModel):
    id: str
    full_name: str
    age: int
    blood_group: str
    organ_needed: List[str]
    urgency: str
    status: str
    created_at: str

    class Config:
        from_attributes = True


class OrganRequestOut(BaseModel):
    id: str
    donor_id: Optional[str]
    recipient_id: str
    organ_type: str
    status: str
    match_compatibility: Optional[float]
    request_date: str
    matched_date: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class DonorCreateByHospital(BaseModel):
    full_name: str
    age: int
    blood_group: str
    location: str
    organs_selected: List[str]
    medical_history: Optional[str] = None
    emergency_contact: Optional[str] = None


class DonorOut(BaseModel):
    id: str
    full_name: str
    age: int
    blood_group: str
    location: str
    hospital_id: Optional[str] = None
    organs_selected: List[str]
    donation_mode: Optional[str] = "general"
    relative_recipient_email: Optional[str] = None
    is_deceased: bool = False
    deceased_at: Optional[str] = None
    status: str
    created_at: str


class RecipientCreateByHospital(BaseModel):
    full_name: str
    age: int
    blood_group: str
    medical_condition: str
    organ_needed: List[str]
    urgency: str = "standard"


class MatchCandidateOut(BaseModel):
    donor_id: str
    donor_name: str
    blood_group: str
    location: str
    organs_selected: List[str]
    recipient_id: str
    organ_match_count: int
    score: float


class MatchAssignRequest(BaseModel):
    donor_id: str
    recipient_id: str
    organ_type: Optional[str] = None
    notes: Optional[str] = None


class DonorDeathUpdateRequest(BaseModel):
    is_deceased: bool = True


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


def _validate_donor_payload(payload: DonorCreateByHospital) -> None:
    if len(payload.full_name.strip()) < 2 or len(payload.full_name.strip()) > 120:
        raise HTTPException(status_code=400, detail="Full name must be between 2 and 120 characters")
    if payload.age < 18 or payload.age > 75:
        raise HTTPException(status_code=400, detail="Age must be between 18 and 75")
    if payload.blood_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(status_code=400, detail="Invalid blood group")
    if len(payload.location.strip()) < 2:
        raise HTTPException(status_code=400, detail="Location is too short")
    if not payload.organs_selected:
        raise HTTPException(status_code=400, detail="Please select at least one organ")
    invalid = [o for o in payload.organs_selected if o not in ALLOWED_ORGANS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid organs selected: {', '.join(invalid)}")


def _validate_recipient_payload(payload: RecipientCreateByHospital) -> None:
    if len(payload.full_name.strip()) < 2 or len(payload.full_name.strip()) > 120:
        raise HTTPException(status_code=400, detail="Full name must be between 2 and 120 characters")
    if payload.age < 10 or payload.age > 100:
        raise HTTPException(status_code=400, detail="Age must be between 10 and 100")
    if payload.blood_group not in ALLOWED_BLOOD_GROUPS:
        raise HTTPException(status_code=400, detail="Invalid blood group")
    if not payload.medical_condition.strip():
        raise HTTPException(status_code=400, detail="Medical condition is required")
    if not payload.organ_needed:
        raise HTTPException(status_code=400, detail="Please select at least one organ")
    invalid = [o for o in payload.organ_needed if o not in ALLOWED_ORGANS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid organs needed: {', '.join(invalid)}")
    if payload.urgency not in ["urgent", "high", "standard"]:
        raise HTTPException(status_code=400, detail="Invalid urgency level")


def _compatibility_score(recipient: Recipient, donor: Donor) -> float:
    blood_match = 1.0 if donor.blood_group == recipient.blood_group else 0.5
    donor_organs = set(donor.organs_selected or [])
    needed_organs = set(recipient.organ_needed or [])
    overlap = len(donor_organs.intersection(needed_organs))
    organ_match = min(1.0, overlap / max(1, len(needed_organs)))
    urgency_bonus = {"urgent": 0.2, "high": 0.1, "standard": 0.0}.get(recipient.urgency, 0.0)
    return round((blood_match * 0.5) + (organ_match * 0.5) + urgency_bonus, 3)


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=HospitalOut)
async def register_hospital(
    payload: HospitalCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Register or complete a hospital profile"""
    if current_user.role != UserRole.hospital:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only hospital users can register a hospital",
        )

    # Load existing profile (including placeholder created at auth registration).
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    # Check if registration number already exists (ignore current profile)
    if payload.registration_number:
        result = await db.execute(
            select(Hospital).where(Hospital.registration_number == payload.registration_number)
        )
        existing = result.scalar_one_or_none()
        if existing and (not hospital or existing.id != hospital.id):
            raise HTTPException(status_code=400, detail="Registration number already registered")

    if hospital:
        if payload.hospital_name is not None:
            hospital.hospital_name = payload.hospital_name
        if payload.registration_number is not None:
            hospital.registration_number = payload.registration_number
        if payload.city is not None:
            hospital.city = payload.city
        if payload.state is not None:
            hospital.state = payload.state
        if payload.phone is not None:
            hospital.phone = payload.phone
        if payload.email is not None:
            hospital.email = payload.email
        if payload.website is not None:
            hospital.website = payload.website
        if payload.bed_capacity is not None:
            hospital.bed_capacity = payload.bed_capacity
        if payload.specializations is not None:
            hospital.specializations = payload.specializations
        hospital.updated_at = datetime.utcnow()
        await db.flush()
    else:
        hospital = Hospital(
            user_id=current_user.id,
            hospital_name=payload.hospital_name,
            registration_number=payload.registration_number,
            city=payload.city,
            state=payload.state,
            phone=payload.phone,
            email=payload.email,
            website=payload.website,
            bed_capacity=payload.bed_capacity,
            specializations=payload.specializations,
        )
        db.add(hospital)
        await db.flush()

    return HospitalOut(
        id=str(hospital.id),
        hospital_name=hospital.hospital_name,
        registration_number=hospital.registration_number,
        city=hospital.city,
        state=hospital.state,
        phone=hospital.phone,
        email=hospital.email,
        website=hospital.website,
        bed_capacity=hospital.bed_capacity,
        specializations=hospital.specializations,
        is_verified=hospital.is_verified,
        created_at=hospital.created_at.isoformat(),
    )


@router.get("/me", response_model=HospitalOut)
async def get_my_hospital(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's hospital info"""
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered"
        )

    return HospitalOut(
        id=str(hospital.id),
        hospital_name=hospital.hospital_name,
        registration_number=hospital.registration_number,
        city=hospital.city,
        state=hospital.state,
        phone=hospital.phone,
        email=hospital.email,
        website=hospital.website,
        bed_capacity=hospital.bed_capacity,
        specializations=hospital.specializations,
        is_verified=hospital.is_verified,
        created_at=hospital.created_at.isoformat(),
    )


@router.put("/me", response_model=HospitalOut)
async def update_my_hospital(
    payload: HospitalUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update hospital information"""
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered"
        )

    if payload.hospital_name is not None:
        hospital.hospital_name = payload.hospital_name
    if payload.phone is not None:
        hospital.phone = payload.phone
    if payload.website is not None:
        hospital.website = payload.website
    if payload.bed_capacity is not None:
        hospital.bed_capacity = payload.bed_capacity
    if payload.specializations is not None:
        hospital.specializations = payload.specializations

    hospital.updated_at = datetime.utcnow()
    await db.flush()

    return HospitalOut(
        id=str(hospital.id),
        hospital_name=hospital.hospital_name,
        registration_number=hospital.registration_number,
        city=hospital.city,
        state=hospital.state,
        phone=hospital.phone,
        email=hospital.email,
        website=hospital.website,
        bed_capacity=hospital.bed_capacity,
        specializations=hospital.specializations,
        is_verified=hospital.is_verified,
        created_at=hospital.created_at.isoformat(),
    )


@router.get("/recipients", response_model=List[RecipientOut])
async def list_recipients(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List recipients at this hospital"""
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    # Admin can access all recipients even without a hospital profile.
    urgency_rank = case(
        (Recipient.urgency == "urgent", 0),
        (Recipient.urgency == "high", 1),
        (Recipient.urgency == "standard", 2),
        else_=3,
    )

    if hospital:
        # Show both recipients assigned to this hospital and unassigned recipients
        # so hospital staff can act on incoming profiles not yet linked to a hospital.
        recipients_result = await db.execute(
            select(Recipient)
            .where(or_(Recipient.hospital_id == hospital.id, Recipient.hospital_id.is_(None)))
            .order_by(urgency_rank, desc(Recipient.created_at))
        )
    elif current_user.role == UserRole.admin:
        recipients_result = await db.execute(
            select(Recipient).order_by(urgency_rank, desc(Recipient.created_at))
        )
    else:
        # Keep dashboard stable for hospital users who have not completed hospital registration.
        return []

    recipients = recipients_result.scalars().all()
    if recipients:
        recipient_user_ids = [r.user_id for r in recipients if r.user_id]
        active_users_result = await db.execute(
            select(User.id).where(User.id.in_(recipient_user_ids)).where(User.is_active == True)
        )
        active_user_ids = {uid for uid in active_users_result.scalars().all()}
        recipients = [r for r in recipients if r.user_id in active_user_ids]

    return [
        RecipientOut(
            id=str(r.id),
            full_name=r.full_name or "Unknown",
            age=int(r.age) if r.age is not None else 0,
            blood_group=r.blood_group or "N/A",
            organ_needed=r.organ_needed or [],
            urgency=r.urgency or "standard",
            status=r.status or "pending",
            created_at=r.created_at.isoformat(),
        )
        for r in recipients
    ]


@router.get("/directory")
async def hospital_directory(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List verified hospitals and state/city options for donor/recipient forms."""
    if current_user.role not in [UserRole.hospital, UserRole.admin, UserRole.donor, UserRole.recipient]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Authenticated access required")

    result = await db.execute(
        select(Hospital).where(Hospital.is_verified == True).order_by(Hospital.state, Hospital.city, Hospital.hospital_name)
    )
    hospitals = result.scalars().all()

    states = sorted({(h.state or "").strip() for h in hospitals if (h.state or "").strip()})
    cities_by_state = {
        state: sorted({(h.city or "").strip() for h in hospitals if (h.state or "").strip() == state and (h.city or "").strip()})
        for state in states
    }

    return {
        "hospitals": [
            {
                "id": str(h.id),
                "hospital_name": h.hospital_name,
                "city": h.city,
                "state": h.state,
            }
            for h in hospitals
        ],
        "states": states,
        "cities_by_state": cities_by_state,
    }


@router.get("/organ-requests", response_model=List[OrganRequestOut])
async def list_organ_requests(
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List organ requests for this hospital"""
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered"
        )

    # Get organ requests for recipients at this hospital
    query = select(OrganRequest).join(Recipient).where(Recipient.hospital_id == hospital.id)

    if status_filter:
        query = query.where(OrganRequest.status == status_filter)

    query = query.order_by(desc(OrganRequest.request_date))
    requests_result = await db.execute(query)
    requests = requests_result.scalars().all()

    return [
        OrganRequestOut(
            id=str(r.id),
            donor_id=str(r.donor_id) if r.donor_id else None,
            recipient_id=str(r.recipient_id),
            organ_type=r.organ_type,
            status=r.status,
            match_compatibility=r.match_compatibility,
            request_date=r.request_date.isoformat(),
            matched_date=r.matched_date.isoformat() if r.matched_date else None,
            notes=r.notes,
        )
        for r in requests
    ]


@router.post("/organ-requests/{request_id}/accept")
async def accept_organ_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Accept an organ request"""
    result = await db.execute(select(OrganRequest).where(OrganRequest.id == request_id))
    organ_request = result.scalar_one_or_none()

    if not organ_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )

    # Verify hospital
    hospital_result = await db.execute(
        select(Hospital).where(Hospital.user_id == current_user.id)
    )
    hospital = hospital_result.scalar_one_or_none()

    if not hospital:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Hospital not registered"
        )

    # Verify request belongs to hospital
    recipient_result = await db.execute(
        select(Recipient).where(Recipient.id == organ_request.recipient_id)
    )
    recipient = recipient_result.scalar_one_or_none()

    if not recipient or recipient.hospital_id != hospital.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Request does not belong to your hospital",
        )

    organ_request.status = "accepted"
    organ_request.matched_date = datetime.utcnow()
    await db.flush()

    return {"message": "Request accepted", "request_id": str(request_id)}


@router.post("/organ-requests/{request_id}/reject")
async def reject_organ_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject an organ request"""
    result = await db.execute(select(OrganRequest).where(OrganRequest.id == request_id))
    organ_request = result.scalar_one_or_none()

    if not organ_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Request not found"
        )

    organ_request.status = "rejected"
    await db.flush()

    return {"message": "Request rejected", "request_id": str(request_id)}


@router.get("/analytics")
async def hospital_analytics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()

    if hospital:
        recipients_count = (
            await db.execute(select(func.count(Recipient.id)).where(Recipient.hospital_id == hospital.id))
        ).scalar() or 0

        requests_count = (
            await db.execute(
                select(func.count(OrganRequest.id))
                .join(Recipient)
                .where(Recipient.hospital_id == hospital.id)
            )
        ).scalar() or 0

        urgent_count = (
            await db.execute(
                select(func.count(Recipient.id))
                .where(Recipient.hospital_id == hospital.id)
                .where(Recipient.urgency == "urgent")
            )
        ).scalar() or 0

        matched_count = (
            await db.execute(
                select(func.count(OrganRequest.id))
                .join(Recipient)
                .where(Recipient.hospital_id == hospital.id)
                .where(OrganRequest.status.in_(["matched", "accepted", "completed"]))
            )
        ).scalar() or 0
    elif current_user.role == UserRole.admin:
        recipients_count = (await db.execute(select(func.count(Recipient.id)))).scalar() or 0

        requests_count = (await db.execute(select(func.count(OrganRequest.id)))).scalar() or 0

        urgent_count = (
            await db.execute(
                select(func.count(Recipient.id)).where(Recipient.urgency == "urgent")
            )
        ).scalar() or 0

        matched_count = (
            await db.execute(
                select(func.count(OrganRequest.id)).where(
                    OrganRequest.status.in_(["matched", "accepted", "completed"])
                )
            )
        ).scalar() or 0
    else:
        # Keep dashboard stable for hospital users who have not completed hospital registration.
        recipients_count = 0
        requests_count = 0
        urgent_count = 0
        matched_count = 0

    return {
        "total_recipients": recipients_count,
        "total_organ_requests": requests_count,
        "urgent_cases": urgent_count,
        "matched_requests": matched_count,
    }


@router.get("/donors", response_model=List[DonorOut])
async def list_donors(
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = None,
    blood_group: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [UserRole.hospital, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")

    query = select(Donor)
    if status_filter:
        query = query.where(Donor.status == status_filter)
    if blood_group:
        query = query.where(Donor.blood_group == blood_group)

    query = query.order_by(desc(Donor.created_at))
    result = await db.execute(query)
    donors = result.scalars().all()

    return [
        DonorOut(
            id=str(d.id),
            full_name=d.full_name,
            age=d.age,
            blood_group=d.blood_group,
            location=d.location,
            hospital_id=str(d.hospital_id) if d.hospital_id else None,
            organs_selected=d.organs_selected or [],
            donation_mode=d.donation_mode or "general",
            relative_recipient_email=d.relative_recipient_email,
            is_deceased=bool(d.is_deceased),
            deceased_at=d.deceased_at.isoformat() if d.deceased_at else None,
            status=d.status.value if hasattr(d.status, "value") else str(d.status),
            created_at=d.created_at.isoformat(),
        )
        for d in donors
    ]


@router.post("/donors", response_model=DonorOut, status_code=status.HTTP_201_CREATED)
async def add_donor_by_hospital(
    payload: DonorCreateByHospital,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [UserRole.hospital, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")

    _validate_donor_payload(payload)

    donor = Donor(
        user_id=current_user.id,
        full_name=payload.full_name.strip(),
        age=payload.age,
        blood_group=payload.blood_group,
        location=payload.location.strip(),
        organs_selected=payload.organs_selected,
        medical_history=(payload.medical_history or "").strip() or None,
        emergency_contact=(payload.emergency_contact or "").strip() or None,
        consent_agreed=True,
        status=DonorStatus.pending,
    )
    db.add(donor)
    await db.flush()

    return DonorOut(
        id=str(donor.id),
        full_name=donor.full_name,
        age=donor.age,
        blood_group=donor.blood_group,
        location=donor.location,
        hospital_id=str(donor.hospital_id) if donor.hospital_id else None,
        organs_selected=donor.organs_selected or [],
        donation_mode=donor.donation_mode or "general",
        relative_recipient_email=donor.relative_recipient_email,
        is_deceased=bool(donor.is_deceased),
        deceased_at=donor.deceased_at.isoformat() if donor.deceased_at else None,
        status=donor.status.value,
        created_at=donor.created_at.isoformat(),
    )


@router.post("/recipients", response_model=RecipientOut, status_code=status.HTTP_201_CREATED)
async def add_recipient_by_hospital(
    payload: RecipientCreateByHospital,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [UserRole.hospital, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")

    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered")

    _validate_recipient_payload(payload)

    recipient = Recipient(
        user_id=current_user.id,
        full_name=payload.full_name.strip(),
        age=payload.age,
        blood_group=payload.blood_group,
        medical_condition=payload.medical_condition.strip(),
        organ_needed=payload.organ_needed,
        urgency=payload.urgency,
        hospital_id=hospital.id,
        status="pending",
    )
    db.add(recipient)
    await db.flush()

    return RecipientOut(
        id=str(recipient.id),
        full_name=recipient.full_name,
        age=recipient.age,
        blood_group=recipient.blood_group,
        organ_needed=recipient.organ_needed,
        urgency=recipient.urgency,
        status=recipient.status,
        created_at=recipient.created_at.isoformat(),
    )


@router.patch("/recipients/{recipient_id}/urgency", response_model=RecipientOut)
async def set_recipient_urgency(
    recipient_id: str,
    urgency: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if urgency not in ["urgent", "high", "standard"]:
        raise HTTPException(status_code=400, detail="Invalid urgency level")

    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered")

    recipient_result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    if recipient.hospital_id != hospital.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recipient does not belong to your hospital")

    recipient.urgency = urgency
    recipient.updated_at = datetime.utcnow()
    await db.flush()

    return RecipientOut(
        id=str(recipient.id),
        full_name=recipient.full_name,
        age=recipient.age,
        blood_group=recipient.blood_group,
        organ_needed=recipient.organ_needed,
        urgency=recipient.urgency,
        status=recipient.status,
        created_at=recipient.created_at.isoformat(),
    )


@router.get("/matches/{recipient_id}", response_model=List[MatchCandidateOut])
async def find_matches_for_recipient(
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered")

    recipient_result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")
    if recipient.hospital_id not in (hospital.id, None):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recipient does not belong to your hospital")

    donors_result = await db.execute(
        select(Donor)
        .where(Donor.status == DonorStatus.approved)
        .where(Donor.donation_mode != "relative")
        .where((Donor.donation_mode != "after_death") | (Donor.is_deceased == True))
        .order_by(desc(Donor.created_at))
        .limit(100)
    )
    donors = donors_result.scalars().all()

    if donors:
        donor_user_ids = [d.user_id for d in donors if d.user_id]
        active_users_result = await db.execute(
            select(User.id).where(User.id.in_(donor_user_ids)).where(User.is_active == True)
        )
        active_user_ids = {uid for uid in active_users_result.scalars().all()}
        donors = [d for d in donors if d.user_id in active_user_ids]

    candidates = []
    needed_organs = set(recipient.organ_needed or [])
    for donor in donors:
        donor_organs = set(donor.organs_selected or [])
        overlap = len(donor_organs.intersection(needed_organs))
        if overlap == 0:
            continue
        candidates.append(
            MatchCandidateOut(
                donor_id=str(donor.id),
                donor_name=donor.full_name,
                blood_group=donor.blood_group,
                location=donor.location,
                organs_selected=donor.organs_selected or [],
                recipient_id=str(recipient.id),
                organ_match_count=overlap,
                score=_compatibility_score(recipient, donor),
            )
        )

    candidates.sort(key=lambda c: (-c.score, -c.organ_match_count, c.location))
    return candidates[:20]


@router.post("/matches/assign")
async def assign_match(
    payload: MatchAssignRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [UserRole.hospital, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")

    try:
        donor_uuid = uuid.UUID(payload.donor_id)
        recipient_uuid = uuid.UUID(payload.recipient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid donor or recipient id")

    hospital = None
    if current_user.role == UserRole.hospital:
        hospital_result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
        hospital = hospital_result.scalar_one_or_none()
        if not hospital:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered")

    donor_result = await db.execute(select(Donor).where(Donor.id == donor_uuid))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    recipient_result = await db.execute(select(Recipient).where(Recipient.id == recipient_uuid))
    recipient = recipient_result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    if hospital and recipient.hospital_id not in (hospital.id, None):
        raise HTTPException(status_code=403, detail="Recipient does not belong to your hospital")

    donor_organs = set(donor.organs_selected or [])
    needed_organs = set(recipient.organ_needed or [])
    overlap = [o for o in donor_organs.intersection(needed_organs)]
    if not overlap:
        raise HTTPException(status_code=400, detail="Selected donor and recipient are not organ-compatible")

    organ_type = payload.organ_type if payload.organ_type in overlap else overlap[0]
    compatibility = _compatibility_score(recipient, donor)

    request = OrganRequest(
        donor_id=donor.id,
        recipient_id=recipient.id,
        organ_type=organ_type,
        status="matched",
        match_compatibility=compatibility,
        matched_date=datetime.utcnow(),
        notes=payload.notes or "Hospital assigned match",
    )
    db.add(request)

    recipient.status = "inactive"
    recipient.updated_at = datetime.utcnow()
    donor.updated_at = datetime.utcnow()

    await db.flush()
    await db.commit()
    db.add(request)

    # Inactivate both donor and recipient user accounts
    donor_user_result = await db.execute(select(User).where(User.id == donor.user_id))
    donor_user = donor_user_result.scalar_one_or_none()
    
    recipient_user_result = await db.execute(select(User).where(User.id == recipient.user_id))
    recipient_user = recipient_user_result.scalar_one_or_none()
    
    if donor_user:
        donor_user.is_active = False
    
    if recipient_user:
        recipient_user.is_active = False

    recipient.status = "matched"
    recipient.updated_at = datetime.utcnow()
    donor.updated_at = datetime.utcnow()

    await db.flush()
    await db.commit()

    return {
        "message": "Match assigned successfully",
        "organ_request_id": str(request.id),
        "recipient_id": str(recipient.id),
        "donor_id": str(donor.id),
        "organ_type": organ_type,
    }


@router.patch("/donors/{donor_id}/death")
async def update_donor_death_status(
    donor_id: str,
    payload: DonorDeathUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if current_user.role not in [UserRole.hospital, UserRole.admin]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital access required")

    try:
        donor_uuid = uuid.UUID(donor_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid donor id")

    hospital = None
    if current_user.role == UserRole.hospital:
        hospital_result = await db.execute(select(Hospital).where(Hospital.user_id == current_user.id))
        hospital = hospital_result.scalar_one_or_none()
        if not hospital:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Hospital not registered")

    donor_result = await db.execute(select(Donor).where(Donor.id == donor_uuid))
    donor = donor_result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    if hospital and donor.hospital_id != hospital.id:
        raise HTTPException(status_code=403, detail="Donor is not assigned to your hospital")

    donor.is_deceased = bool(payload.is_deceased)
    donor.deceased_at = datetime.utcnow() if payload.is_deceased else None
    donor.updated_at = datetime.utcnow()

    await db.flush()
    await db.commit()

    return {
        "message": "Donor death status updated",
        "donor_id": str(donor.id),
        "is_deceased": donor.is_deceased,
        "deceased_at": donor.deceased_at.isoformat() if donor.deceased_at else None,
    }
