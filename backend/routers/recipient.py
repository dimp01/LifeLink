"""
Recipient verification routes
Handles recipient verification form submissions and status
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from database import get_db
from auth import get_current_user
from services import RecipientService
from models import User, RecipientVerification

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
