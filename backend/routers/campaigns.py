from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime
import uuid

from database import get_db
from models import Campaign, CampaignParticipant, User
from auth import get_current_user

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


class CampaignCreate(BaseModel):
    title: str
    description: str
    content: Optional[str] = None
    icon: str = "🎯"
    campaign_type: str = "challenge"
    target_participants: int = 100


class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None
    icon: Optional[str] = None
    is_active: Optional[bool] = None
    target_participants: Optional[int] = None


class CampaignParticipantOut(BaseModel):
    id: str
    user_id: str
    joined_at: str

    class Config:
        from_attributes = True


class CampaignOut(BaseModel):
    id: str
    title: str
    description: str
    content: Optional[str]
    icon: str
    campaign_type: str
    target_participants: int
    is_active: bool
    participant_count: int = 0
    user_joined: bool = False
    created_at: str
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


@router.get("", response_model=List[CampaignOut])
async def list_campaigns(
    skip: int = 0,
    limit: int = 20,
    active_only: bool = True,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all campaigns"""
    query = select(Campaign)
    if active_only:
        query = query.where(Campaign.is_active == True)
    query = query.order_by(desc(Campaign.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    campaigns = result.scalars().all()

    # Get participant counts and check if user joined
    output = []
    for campaign in campaigns:
        participant_count = len(campaign.participants) if campaign.participants else 0
        user_joined = any(p.user_id == current_user.id for p in (campaign.participants or []))
        output.append(
            CampaignOut(
                id=str(campaign.id),
                title=campaign.title,
                description=campaign.description,
                content=campaign.content,
                icon=campaign.icon,
                campaign_type=campaign.campaign_type,
                target_participants=campaign.target_participants,
                is_active=campaign.is_active,
                participant_count=participant_count,
                user_joined=user_joined,
                created_at=campaign.created_at.isoformat(),
                created_by=str(campaign.created_by) if campaign.created_by else None,
            )
        )
    return output


@router.get("/{campaign_id}", response_model=CampaignOut)
async def get_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get campaign details"""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    participant_count = len(campaign.participants) if campaign.participants else 0
    user_joined = any(p.user_id == current_user.id for p in (campaign.participants or []))

    return CampaignOut(
        id=str(campaign.id),
        title=campaign.title,
        description=campaign.description,
        content=campaign.content,
        icon=campaign.icon,
        campaign_type=campaign.campaign_type,
        target_participants=campaign.target_participants,
        is_active=campaign.is_active,
        participant_count=participant_count,
        user_joined=user_joined,
        created_at=campaign.created_at.isoformat(),
        created_by=str(campaign.created_by) if campaign.created_by else None,
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CampaignOut)
async def create_campaign(
    payload: CampaignCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new campaign (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can create campaigns")

    campaign = Campaign(
        title=payload.title,
        description=payload.description,
        content=payload.content,
        icon=payload.icon,
        campaign_type=payload.campaign_type,
        target_participants=payload.target_participants,
        created_by=current_user.id,
    )
    db.add(campaign)
    await db.flush()

    return CampaignOut(
        id=str(campaign.id),
        title=campaign.title,
        description=campaign.description,
        content=campaign.content,
        icon=campaign.icon,
        campaign_type=campaign.campaign_type,
        target_participants=campaign.target_participants,
        is_active=campaign.is_active,
        participant_count=0,
        user_joined=False,
        created_at=campaign.created_at.isoformat(),
        created_by=str(campaign.created_by),
    )


@router.put("/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a campaign (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can update campaigns")

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    if payload.title is not None:
        campaign.title = payload.title
    if payload.description is not None:
        campaign.description = payload.description
    if payload.content is not None:
        campaign.content = payload.content
    if payload.icon is not None:
        campaign.icon = payload.icon
    if payload.is_active is not None:
        campaign.is_active = payload.is_active
    if payload.target_participants is not None:
        campaign.target_participants = payload.target_participants

    campaign.updated_at = datetime.utcnow()
    await db.flush()

    participant_count = len(campaign.participants) if campaign.participants else 0

    return CampaignOut(
        id=str(campaign.id),
        title=campaign.title,
        description=campaign.description,
        content=campaign.content,
        icon=campaign.icon,
        campaign_type=campaign.campaign_type,
        target_participants=campaign.target_participants,
        is_active=campaign.is_active,
        participant_count=participant_count,
        user_joined=False,
        created_at=campaign.created_at.isoformat(),
        created_by=str(campaign.created_by) if campaign.created_by else None,
    )


@router.delete("/{campaign_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a campaign (admin only)"""
    from models import UserRole

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only admins can delete campaigns")

    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    await db.delete(campaign)
    await db.commit()


@router.post("/{campaign_id}/join")
async def join_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Join a campaign"""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    # Check if already joined
    existing = await db.execute(
        select(CampaignParticipant).where(
            (CampaignParticipant.campaign_id == campaign_id)
            & (CampaignParticipant.user_id == current_user.id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already joined this campaign")

    participant = CampaignParticipant(campaign_id=campaign_id, user_id=current_user.id)
    db.add(participant)
    await db.commit()

    return {"message": "Successfully joined campaign", "campaign_id": str(campaign_id)}


@router.post("/{campaign_id}/leave")
async def leave_campaign(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Leave a campaign"""
    result = await db.execute(
        select(CampaignParticipant).where(
            (CampaignParticipant.campaign_id == campaign_id)
            & (CampaignParticipant.user_id == current_user.id)
        )
    )
    participant = result.scalar_one_or_none()

    if not participant:
        raise HTTPException(status_code=400, detail="Not a member of this campaign")

    await db.delete(participant)
    await db.commit()

    return {"message": "Successfully left campaign"}


@router.get("/{campaign_id}/participants", response_model=List[CampaignParticipantOut])
async def get_campaign_participants(
    campaign_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get campaign participants"""
    result = await db.execute(select(Campaign).where(Campaign.id == campaign_id))
    campaign = result.scalar_one_or_none()

    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campaign not found")

    participants_result = await db.execute(
        select(CampaignParticipant).where(CampaignParticipant.campaign_id == campaign_id)
    )
    participants = participants_result.scalars().all()

    return [
        CampaignParticipantOut(
            id=str(p.id), user_id=str(p.user_id), joined_at=p.joined_at.isoformat()
        )
        for p in participants
    ]
