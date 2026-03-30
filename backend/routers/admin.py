from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from datetime import datetime
import uuid

from database import get_db
from models import Donor, DonorStatus, User, AwarenessContent, ContentType, AuditLog, MLPrediction, ChatLog, Recipient, Hospital, OrganRequest
from auth import get_current_admin, get_current_hospital_or_admin
import ml_pipeline

router = APIRouter()


class DonorStatusUpdate(BaseModel):
    status: DonorStatus
    reason: Optional[str] = None


class AwarenessCreate(BaseModel):
    title: str
    content: str
    type: ContentType


class RecipientCreateByAdmin(BaseModel):
    full_name: str
    age: int
    blood_group: str
    medical_condition: str
    organ_needed: list[str]
    urgency: str = "standard"
    status: str = "pending"
    user_id: Optional[str] = None
    hospital_id: Optional[str] = None


class RecipientStatusUpdate(BaseModel):
    status: str


class RecipientUrgencyUpdate(BaseModel):
    urgency: str


class HospitalCreateByAdmin(BaseModel):
    hospital_name: str
    registration_number: Optional[str] = None
    city: str
    state: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    bed_capacity: Optional[int] = None
    specializations: Optional[list[str]] = None
    is_verified: bool = False
    user_id: Optional[str] = None


class HospitalStatusUpdate(BaseModel):
    # approved => verified=true, suspended => verified=false
    status: str


class UserDeleteRequest(BaseModel):
    reason: Optional[str] = None


@router.get("/donors")
async def list_all_donors(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    query = select(Donor)
    if status:
        query = query.where(Donor.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    donors = result.scalars().all()

    return [
        {
            "id": str(d.id),
            "full_name": d.full_name,
            "age": d.age,
            "blood_group": d.blood_group,
            "location": d.location,
            "organs_selected": d.organs_selected,
            "status": d.status.value,
            "created_at": d.created_at.isoformat(),
            # "email": d.user.email if d.user and d.user.email else 'None',
        }
        for d in donors
    ]


@router.get("/recipients")
async def list_all_recipients(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    query = select(Recipient)
    if status:
        query = query.where(Recipient.status == status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    recipients = result.scalars().all()

    return [
        {
            "id": str(r.id),
            "user_id": str(r.user_id),
            "full_name": r.full_name,
            "age": r.age,
            "blood_group": r.blood_group,
            "medical_condition": r.medical_condition,
            "organ_needed": r.organ_needed,
            "urgency": r.urgency,
            "status": r.status,
            "hospital_id": str(r.hospital_id) if r.hospital_id else None,
            "created_at": r.created_at.isoformat(),
            "updated_at": r.updated_at.isoformat(),
            # "email": r.user.email if r.user and r.user.email else 'None',
        }
        for r in recipients
    ]


@router.get("/hospitals")
async def list_all_hospitals(
    verified: Optional[bool] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    query = select(Hospital)
    if verified is not None:
        query = query.where(Hospital.is_verified == verified)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    hospitals = result.scalars().all()

    return [
        {
            "id": str(h.id),
            "user_id": str(h.user_id),
            "hospital_name": h.hospital_name,
            "registration_number": h.registration_number,
            "city": h.city,
            "state": h.state,
            "phone": h.phone,
            "email": h.email,
            "website": h.website,
            "bed_capacity": h.bed_capacity,
            "specializations": h.specializations,
            "is_verified": h.is_verified,
            "created_at": h.created_at.isoformat(),
            "updated_at": h.updated_at.isoformat(),
        }
        for h in hospitals
    ]


@router.post("/recipients", status_code=201)
async def create_recipient_by_admin(
    payload: RecipientCreateByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    allowed_urgency = {"standard", "high", "urgent"}
    allowed_status = {"pending", "approved", "rejected", "matched", "completed"}

    if payload.urgency not in allowed_urgency:
        raise HTTPException(status_code=400, detail="Invalid urgency")
    if payload.status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid status")
    if payload.age < 10 or payload.age > 100:
        raise HTTPException(status_code=400, detail="Age must be between 10 and 100")
    if not payload.organ_needed:
        raise HTTPException(status_code=400, detail="At least one organ is required")

    user_id = current_user.id
    if payload.user_id:
        try:
            user_id = uuid.UUID(payload.user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id")

    hospital_id = None
    if payload.hospital_id:
        try:
            hospital_id = uuid.UUID(payload.hospital_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid hospital_id")

    recipient = Recipient(
        user_id=user_id,
        full_name=payload.full_name.strip(),
        age=payload.age,
        blood_group=payload.blood_group,
        medical_condition=payload.medical_condition.strip(),
        organ_needed=payload.organ_needed,
        urgency=payload.urgency,
        status=payload.status,
        hospital_id=hospital_id,
    )
    db.add(recipient)
    await db.commit()

    return {"message": "Recipient created successfully", "id": str(recipient.id)}


@router.put("/recipients/{recipient_id}/status")
async def update_recipient_status(
    recipient_id: str,
    payload: RecipientStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    allowed_status = {"pending", "approved", "rejected", "matched", "completed"}
    if payload.status not in allowed_status:
        raise HTTPException(status_code=400, detail="Invalid status")

    try:
        rid = uuid.UUID(recipient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipient_id")

    result = await db.execute(select(Recipient).where(Recipient.id == rid))
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.status = payload.status
    recipient.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action="RECIPIENT_STATUS_UPDATED",
        details={"recipient_id": recipient_id, "new_status": payload.status},
    ))
    await db.commit()
    return {"message": "Recipient status updated", "status": payload.status}


@router.patch("/recipients/{recipient_id}/urgency")
async def update_recipient_urgency(
    recipient_id: str,
    payload: RecipientUrgencyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    allowed_urgency = {"standard", "high", "urgent"}
    if payload.urgency not in allowed_urgency:
        raise HTTPException(status_code=400, detail="Invalid urgency")

    try:
        rid = uuid.UUID(recipient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipient_id")

    result = await db.execute(select(Recipient).where(Recipient.id == rid))
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    recipient.urgency = payload.urgency
    recipient.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action="RECIPIENT_URGENCY_UPDATED",
        details={"recipient_id": recipient_id, "new_urgency": payload.urgency},
    ))
    await db.commit()
    return {"message": "Recipient urgency updated", "urgency": payload.urgency}


@router.delete("/recipients/{recipient_id}")
async def delete_recipient_by_admin(
    recipient_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        rid = uuid.UUID(recipient_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid recipient_id")

    result = await db.execute(select(Recipient).where(Recipient.id == rid))
    recipient = result.scalar_one_or_none()
    if not recipient:
        raise HTTPException(status_code=404, detail="Recipient not found")

    req_result = await db.execute(select(OrganRequest).where(OrganRequest.recipient_id == rid))
    for req in req_result.scalars().all():
        await db.delete(req)

    await db.delete(recipient)
    db.add(AuditLog(
        user_id=current_user.id,
        action="RECIPIENT_DELETED",
        details={"recipient_id": recipient_id},
    ))
    await db.commit()
    return {"message": "Recipient deleted"}


@router.post("/hospitals", status_code=201)
async def create_hospital_by_admin(
    payload: HospitalCreateByAdmin,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    hospital_user_id = current_user.id
    if payload.user_id:
        try:
            hospital_user_id = uuid.UUID(payload.user_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid user_id")

    hospital = Hospital(
        user_id=hospital_user_id,
        hospital_name=payload.hospital_name.strip(),
        registration_number=(payload.registration_number or "").strip() or None,
        city=payload.city.strip(),
        state=payload.state.strip(),
        phone=(payload.phone or "").strip() or None,
        email=(payload.email or "").strip() or None,
        website=(payload.website or "").strip() or None,
        bed_capacity=payload.bed_capacity,
        specializations=payload.specializations or [],
        is_verified=payload.is_verified,
    )
    db.add(hospital)
    await db.commit()
    return {"message": "Hospital created successfully", "id": str(hospital.id)}


@router.put("/hospitals/{hospital_id}/status")
async def update_hospital_status(
    hospital_id: str,
    payload: HospitalStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    if payload.status not in {"approved", "suspended"}:
        raise HTTPException(status_code=400, detail="Status must be approved or suspended")

    try:
        hid = uuid.UUID(hospital_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hospital_id")

    result = await db.execute(select(Hospital).where(Hospital.id == hid))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    hospital.is_verified = payload.status == "approved"
    hospital.updated_at = datetime.utcnow()
    db.add(AuditLog(
        user_id=current_user.id,
        action="HOSPITAL_STATUS_UPDATED",
        details={"hospital_id": hospital_id, "new_status": payload.status},
    ))
    await db.commit()
    return {"message": "Hospital status updated", "status": payload.status}


@router.delete("/hospitals/{hospital_id}")
async def delete_hospital_by_admin(
    hospital_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    try:
        hid = uuid.UUID(hospital_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid hospital_id")

    result = await db.execute(select(Hospital).where(Hospital.id == hid))
    hospital = result.scalar_one_or_none()
    if not hospital:
        raise HTTPException(status_code=404, detail="Hospital not found")

    recipients_result = await db.execute(select(Recipient).where(Recipient.hospital_id == hid))
    for recipient in recipients_result.scalars().all():
        recipient.hospital_id = None
        recipient.updated_at = datetime.utcnow()

    await db.delete(hospital)
    db.add(AuditLog(
        user_id=current_user.id,
        action="HOSPITAL_DELETED",
        details={"hospital_id": hospital_id},
    ))
    await db.commit()
    return {"message": "Hospital deleted"}


@router.put("/donors/{donor_id}/status")
async def update_donor_status(
    donor_id: str,
    payload: DonorStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    import uuid as _uuid
    result = await db.execute(select(Donor).where(Donor.id == _uuid.UUID(donor_id)))
    donor = result.scalar_one_or_none()
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    reason = payload.reason.strip() if payload.reason else None
    if payload.status == DonorStatus.rejected and not reason:
        raise HTTPException(status_code=400, detail="Reason is required when rejecting a donor")
    if reason and len(reason) > 500:
        raise HTTPException(status_code=400, detail="Reason exceeds max length of 500")

    donor.status = payload.status
    db.add(AuditLog(
        user_id=current_user.id,
        action=f"DONOR_STATUS_UPDATED",
        details={"donor_id": donor_id, "new_status": payload.status.value, "reason": reason},
    ))
    await db.commit()

    return {
        "message": f"Donor status updated to {payload.status.value}",
        "status": payload.status.value,
        "reason": reason,
    }


@router.get("/analytics")
async def get_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_hospital_or_admin),
):
    # Count donors by status
    total_result = await db.execute(select(func.count(Donor.id)))
    total_donors = total_result.scalar()

    pending_result = await db.execute(
        select(func.count(Donor.id)).where(Donor.status == DonorStatus.pending)
    )
    pending = pending_result.scalar()

    approved_result = await db.execute(
        select(func.count(Donor.id)).where(Donor.status == DonorStatus.approved)
    )
    approved = approved_result.scalar()

    # Count users
    user_result = await db.execute(select(func.count(User.id)))
    total_users = user_result.scalar()

    recipient_result = await db.execute(select(func.count(Recipient.id)))
    total_recipients = recipient_result.scalar()

    hospital_result = await db.execute(select(func.count(Hospital.id)))
    total_hospitals = hospital_result.scalar()

    # Role-wise user distribution
    role_result = await db.execute(
        select(User.role, func.count(User.id)).group_by(User.role)
    )
    users_by_role = {
        (row[0].value if hasattr(row[0], "value") else str(row[0])): row[1]
        for row in role_result.fetchall()
    }

    # Monthly user growth (last 6 months)
    now = datetime.utcnow()
    month_starts = []
    current = datetime(now.year, now.month, 1)
    for _ in range(6):
        month_starts.append(current)
        if current.month == 1:
            current = datetime(current.year - 1, 12, 1)
        else:
            current = datetime(current.year, current.month - 1, 1)
    month_starts = list(reversed(month_starts))

    oldest_month = month_starts[0]
    growth_result = await db.execute(
        select(User.created_at).where(User.created_at >= oldest_month)
    )
    growth_rows = growth_result.fetchall()

    monthly_counts = {
        dt.strftime("%Y-%m"): 0 for dt in month_starts
    }
    for row in growth_rows:
        if not row[0]:
            continue
        key = row[0].strftime("%Y-%m")
        if key in monthly_counts:
            monthly_counts[key] += 1

    users_growth = [
        {
            "month": dt.strftime("%b %Y"),
            "count": monthly_counts[dt.strftime("%Y-%m")],
        }
        for dt in month_starts
    ]

    # Blood group distribution
    bg_result = await db.execute(
        select(Donor.blood_group, func.count(Donor.id)).group_by(Donor.blood_group)
    )
    blood_groups = {row[0]: row[1] for row in bg_result.fetchall()}

    # Region distribution
    region_result = await db.execute(
        select(Donor.location, func.count(Donor.id)).group_by(Donor.location).limit(10)
    )
    regions = [{"region": row[0], "count": row[1]} for row in region_result.fetchall()]

    return {
        "total_donors": total_donors,
        "total_recipients": total_recipients,
        "total_hospitals": total_hospitals,
        "pending_donors": pending,
        "approved_donors": approved,
        "total_users": total_users,
        "users_by_role": users_by_role,
        "users_growth": users_growth,
        "blood_group_distribution": blood_groups,
        "top_regions": regions,
    }


@router.get("/users")
async def list_users_by_admin(
    role: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """List users with filters and pagination for admin user management."""
    if page < 1:
        page = 1
    if page_size < 1:
        page_size = 10
    if page_size > 100:
        page_size = 100

    filters = []

    if role:
        filters.append(User.role == role)

    if status == "active":
        filters.append(User.is_active.is_(True))
    elif status == "inactive":
        filters.append(User.is_active.is_(False))

    if q:
        q_value = f"%{q.strip()}%"
        filters.append(
            (User.email.ilike(q_value)) | (User.full_name.ilike(q_value))
        )

    where_clause = and_(*filters) if filters else None

    total_query = select(func.count(User.id))
    if where_clause is not None:
        total_query = total_query.where(where_clause)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    offset = (page - 1) * page_size
    users_query = select(User).order_by(User.created_at.desc()).offset(offset).limit(page_size)
    if where_clause is not None:
        users_query = users_query.where(where_clause)

    users_result = await db.execute(users_query)
    users = users_result.scalars().all()

    return {
        "items": [
            {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role.value if hasattr(user.role, "value") else str(user.role),
                "is_active": bool(user.is_active),
                "created_at": user.created_at.isoformat() if user.created_at else None,
            }
            for user in users
        ],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": (total + page_size - 1) // page_size,
    }


@router.delete("/users/{user_id}")
async def delete_user_by_admin(
    user_id: str,
    payload: Optional[UserDeleteRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Soft-delete user by deactivating account to avoid relational data loss."""
    try:
        uid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id")

    if uid == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete your own account")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False

    db.add(AuditLog(
        user_id=current_user.id,
        action="USER_DEACTIVATED",
        details={
            "target_user_id": str(uid),
            "target_email": user.email,
            "reason": payload.reason.strip() if payload and payload.reason else None,
        },
    ))
    await db.commit()

    return {"message": "User deactivated successfully"}


@router.post("/awareness", status_code=201)
async def create_awareness_content(
    payload: AwarenessCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    content = AwarenessContent(
        title=payload.title,
        content=payload.content,
        type=payload.type,
        created_by=current_user.id,
    )
    db.add(content)
    await db.commit()
    return {"message": "Content created successfully"}


@router.get("/audit-logs")
async def get_audit_logs(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc()).offset(skip).limit(limit)
    )
    logs = result.scalars().all()
    return [
        {
            "id": str(l.id),
            "user_id": str(l.user_id) if l.user_id else None,
            "action": l.action,
            "details": l.details,
            "timestamp": l.timestamp.isoformat(),
        }
        for l in logs
    ]


@router.get("/chat-logs")
async def get_chat_logs(
    skip: int = 0,
    limit: int = 100,
    classification: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_admin),
):
    """Return all chatbot interaction logs for research evaluation."""
    query = select(ChatLog).order_by(ChatLog.timestamp.desc())
    if classification:
        query = query.where(ChatLog.classification == classification)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()

    # Summary stats
    total_result = await db.execute(select(func.count(ChatLog.id)))
    total = total_result.scalar()

    organ_result = await db.execute(
        select(func.count(ChatLog.id)).where(ChatLog.classification == "organ_related")
    )
    organ_count = organ_result.scalar()

    return {
        "summary": {
            "total_queries": total,
            "organ_related": organ_count,
            "non_organ_related": total - organ_count,
            "rejection_rate": round((total - organ_count) / total, 4) if total > 0 else 0,
        },
        "logs": [
            {
                "id": str(l.id),
                "user_id": str(l.user_id) if l.user_id else None,
                "query": l.query,
                "classification": l.classification,
                "response": l.response,
                "confidence": l.confidence,
                "timestamp": l.timestamp.isoformat(),
            }
            for l in logs
        ],
    }


@router.get("/model-versions")
async def get_model_versions(
    current_user=Depends(get_current_admin),
):
    """Return all model training version history."""
    results = ml_pipeline.load_saved_results()
    versions = results.get("model_versions", [])
    return {
        "total_versions": len(versions),
        "versions": versions,
    }
