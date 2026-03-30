from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_hospital_or_admin
from database import get_db
from matching_service import MatchingService
from models import User, AuditLog

router = APIRouter()


class MatchRequest(BaseModel):
    donor_id: str
    include_survival: bool = False
    top_k: int = 20


@router.post("/match")
async def match_recipients_for_donor(
    payload: MatchRequest,
    current_user: User = Depends(get_current_hospital_or_admin),
    db: AsyncSession = Depends(get_db),
):
    service = MatchingService(db)
    result = await service.rank_recipients_for_donor(
        donor_id=payload.donor_id,
        current_user=current_user,
        include_survival=payload.include_survival,
        top_k=payload.top_k,
    )

    # Follow existing audit logging style used across routers.
    db.add(
        AuditLog(
            user_id=current_user.id,
            action="MATCHING_TRIGGERED",
            details={
                "donor_id": payload.donor_id,
                "recipients_evaluated": result.get("total_candidates", 0),
            },
        )
    )
    await db.commit()

    return result
