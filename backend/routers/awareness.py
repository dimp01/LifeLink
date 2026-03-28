from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from models import AwarenessContent, ContentType

router = APIRouter()


@router.get("")
async def list_awareness_content(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(AwarenessContent)
        .where(AwarenessContent.is_active == True)
        .offset(skip)
        .limit(limit)
    )
    contents = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "content": c.content,
            "type": c.type.value,
            "created_at": c.created_at.isoformat(),
        }
        for c in contents
    ]


@router.get("/{content_type}")
async def list_by_type(
    content_type: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        ctype = ContentType(content_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid type. Use: myth, faq, blog, legal")

    result = await db.execute(
        select(AwarenessContent)
        .where(AwarenessContent.type == ctype, AwarenessContent.is_active == True)
    )
    contents = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "title": c.title,
            "content": c.content,
            "type": c.type.value,
            "created_at": c.created_at.isoformat(),
        }
        for c in contents
    ]
