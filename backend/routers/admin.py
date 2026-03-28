from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from database import get_db
from models import Donor, DonorStatus, User, AwarenessContent, ContentType, AuditLog, MLPrediction, ChatLog
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
        }
        for d in donors
    ]


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
        "pending_donors": pending,
        "approved_donors": approved,
        "total_users": total_users,
        "blood_group_distribution": blood_groups,
        "top_regions": regions,
    }


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
