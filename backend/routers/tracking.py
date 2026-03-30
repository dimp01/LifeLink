from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from datetime import datetime

from database import get_db
from models import OrganRequest, Donor, Recipient, DonorStatus, User
from auth import get_current_user

router = APIRouter(prefix="/tracking", tags=["Tracking"])


class OrganRequestCreate(BaseModel):
    recipient_id: str
    organ_type: str
    notes: Optional[str] = None


class OrganRequestUpdate(BaseModel):
    status: Optional[str] = None
    donor_id: Optional[str] = None
    match_compatibility: Optional[float] = None
    notes: Optional[str] = None


class OrganRequestOut(BaseModel):
    id: str
    donor_id: Optional[str]
    recipient_id: str
    organ_type: str
    status: str
    match_compatibility: Optional[float]
    request_date: str
    matched_date: Optional[str]
    completed_date: Optional[str]
    notes: Optional[str]

    class Config:
        from_attributes = True


class DonationHistory(BaseModel):
    id: str
    donor_name: str
    organ_type: str
    status: str
    donation_date: Optional[str]
    created_at: str


@router.post("/organ-requests", status_code=status.HTTP_201_CREATED, response_model=OrganRequestOut)
async def create_organ_request(
    payload: OrganRequestCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create an organ request (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create organ requests"
        )

    # Verify recipient exists
    recipient_result = await db.execute(select(Recipient).where(Recipient.id == payload.recipient_id))
    recipient = recipient_result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    organ_request = OrganRequest(
        recipient_id=payload.recipient_id,
        organ_type=payload.organ_type,
        notes=payload.notes,
    )
    db.add(organ_request)
    await db.flush()

    return OrganRequestOut(
        id=str(organ_request.id),
        donor_id=str(organ_request.donor_id) if organ_request.donor_id else None,
        recipient_id=str(organ_request.recipient_id),
        organ_type=organ_request.organ_type,
        status=organ_request.status,
        match_compatibility=organ_request.match_compatibility,
        request_date=organ_request.request_date.isoformat(),
        matched_date=organ_request.matched_date.isoformat() if organ_request.matched_date else None,
        completed_date=organ_request.completed_date.isoformat() if organ_request.completed_date else None,
        notes=organ_request.notes,
    )


@router.get("/organ-requests", response_model=List[OrganRequestOut])
async def list_organ_requests(
    current_user: User = Depends(get_current_user),
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List organ requests"""
    from models import UserRole

    query = select(OrganRequest)

    if status_filter:
        query = query.where(OrganRequest.status == status_filter)

    # Non-admins can only see their own vs their recipient
    if current_user.role != UserRole.admin:
        if current_user.role == UserRole.recipient:
            recipient_result = await db.execute(
                select(Recipient).where(Recipient.user_id == current_user.id)
            )
            recipient = recipient_result.scalar_one_or_none()
            if recipient:
                query = query.where(OrganRequest.recipient_id == recipient.id)
            else:
                return []

    query = query.order_by(desc(OrganRequest.request_date))
    result = await db.execute(query)
    requests = result.scalars().all()

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
            completed_date=r.completed_date.isoformat() if r.completed_date else None,
            notes=r.notes,
        )
        for r in requests
    ]


@router.get("/organ-requests/{request_id}", response_model=OrganRequestOut)
async def get_organ_request(
    request_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific organ request"""
    result = await db.execute(select(OrganRequest).where(OrganRequest.id == request_id))
    organ_request = result.scalar_one_or_none()

    if not organ_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    return OrganRequestOut(
        id=str(organ_request.id),
        donor_id=str(organ_request.donor_id) if organ_request.donor_id else None,
        recipient_id=str(organ_request.recipient_id),
        organ_type=organ_request.organ_type,
        status=organ_request.status,
        match_compatibility=organ_request.match_compatibility,
        request_date=organ_request.request_date.isoformat(),
        matched_date=organ_request.matched_date.isoformat() if organ_request.matched_date else None,
        completed_date=organ_request.completed_date.isoformat() if organ_request.completed_date else None,
        notes=organ_request.notes,
    )


@router.put("/organ-requests/{request_id}", response_model=OrganRequestOut)
async def update_organ_request(
    request_id: str,
    payload: OrganRequestUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update organ request (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update requests"
        )

    result = await db.execute(select(OrganRequest).where(OrganRequest.id == request_id))
    organ_request = result.scalar_one_or_none()

    if not organ_request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if payload.status is not None:
        organ_request.status = payload.status
    if payload.donor_id is not None:
        organ_request.donor_id = payload.donor_id
    if payload.match_compatibility is not None:
        organ_request.match_compatibility = payload.match_compatibility
    if payload.notes is not None:
        organ_request.notes = payload.notes

    if payload.status == "matched":
        organ_request.matched_date = datetime.utcnow()
    elif payload.status == "completed":
        organ_request.completed_date = datetime.utcnow()

    await db.flush()

    return OrganRequestOut(
        id=str(organ_request.id),
        donor_id=str(organ_request.donor_id) if organ_request.donor_id else None,
        recipient_id=str(organ_request.recipient_id),
        organ_type=organ_request.organ_type,
        status=organ_request.status,
        match_compatibility=organ_request.match_compatibility,
        request_date=organ_request.request_date.isoformat(),
        matched_date=organ_request.matched_date.isoformat() if organ_request.matched_date else None,
        completed_date=organ_request.completed_date.isoformat() if organ_request.completed_date else None,
        notes=organ_request.notes,
    )


@router.get("/donor/{donor_id}/status")
async def get_donor_status(
    donor_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get donor application status"""
    result = await db.execute(select(Donor).where(Donor.id == donor_id))
    donor = result.scalar_one_or_none()

    if not donor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

    return {
        "donor_id": str(donor.id),
        "status": donor.status.value if hasattr(donor.status, 'value') else donor.status,
        "created_at": donor.created_at.isoformat(),
        "updated_at": donor.updated_at.isoformat(),
    }


@router.get("/recipient/{recipient_id}/status")
async def get_recipient_status(
    recipient_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recipient status and matching info"""
    result = await db.execute(select(Recipient).where(Recipient.id == recipient_id))
    recipient = result.scalar_one_or_none()

    if not recipient:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Recipient not found")

    # Get associated organ requests
    requests_result = await db.execute(
        select(OrganRequest).where(OrganRequest.recipient_id == recipient_id)
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


@router.post("/donor/{donor_id}/status")
async def update_donor_application_status(
    donor_id: str,
    status: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update donor application status (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update donor status"
        )

    if status not in ["pending", "approved", "rejected"]:
        raise HTTPException(status_code=400, detail="Invalid status")

    result = await db.execute(select(Donor).where(Donor.id == donor_id))
    donor = result.scalar_one_or_none()

    if not donor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donor not found")

    donor.status = status
    donor.updated_at = datetime.utcnow()
    await db.flush()

    return {"donor_id": str(donor_id), "status": status}
