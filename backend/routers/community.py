from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload
from datetime import datetime

from database import get_db
from models import CommunityPost, PostLike, User
from auth import get_current_user

router = APIRouter(prefix="/community", tags=["Community"])


class PostCreate(BaseModel):
    title: str
    content: str
    post_type: str = "story"


class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    is_active: Optional[bool] = None


class PostOut(BaseModel):
    id: str
    title: str
    content: str
    post_type: str
    like_count: int
    user_liked: bool = False
    author_id: str
    author_name: Optional[str]
    can_delete: bool = False
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


def _is_super_admin(user: User) -> bool:
    # Project currently has a single seeded super admin account.
    return (user.email or "").strip().lower() == "admin@lifelink.ai"


@router.get("/posts", response_model=List[PostOut])
async def list_posts(
    skip: int = 0,
    limit: int = 20,
    post_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List community posts"""
    query = (
        select(CommunityPost)
        .options(
            selectinload(CommunityPost.author),
            selectinload(CommunityPost.likes),
        )
        .where(CommunityPost.is_active == True)
    )

    if post_type:
        query = query.where(CommunityPost.post_type == post_type)

    query = query.order_by(desc(CommunityPost.created_at)).offset(skip).limit(limit)

    result = await db.execute(query)
    posts = result.scalars().all()

    output = []
    for post in posts:
        user_liked = any(like.user_id == current_user.id for like in (post.likes or []))
        output.append(
            PostOut(
                id=str(post.id),
                title=post.title,
                content=post.content,
                post_type=post.post_type,
                like_count=post.like_count,
                user_liked=user_liked,
                author_id=str(post.user_id),
                author_name=post.author.full_name if post.author else None,
                can_delete=(post.user_id == current_user.id or _is_super_admin(current_user)),
                created_at=post.created_at.isoformat(),
                updated_at=post.updated_at.isoformat(),
            )
        )
    return output


@router.get("/posts/{post_id}", response_model=PostOut)
async def get_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific post"""
    result = await db.execute(
        select(CommunityPost)
        .options(
            selectinload(CommunityPost.author),
            selectinload(CommunityPost.likes),
        )
        .where(CommunityPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post or not post.is_active:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    user_liked = any(like.user_id == current_user.id for like in (post.likes or []))

    return PostOut(
        id=str(post.id),
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        like_count=post.like_count,
        user_liked=user_liked,
        author_id=str(post.user_id),
        author_name=post.author.full_name if post.author else None,
        can_delete=(post.user_id == current_user.id or _is_super_admin(current_user)),
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.post("/posts", status_code=status.HTTP_201_CREATED, response_model=PostOut)
async def create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new community post"""
    if len(payload.title.strip()) < 3:
        raise HTTPException(status_code=400, detail="Title must be at least 3 characters")
    if len(payload.content.strip()) < 10:
        raise HTTPException(status_code=400, detail="Content must be at least 10 characters")

    post = CommunityPost(
        user_id=current_user.id,
        title=payload.title.strip(),
        content=payload.content.strip(),
        post_type=payload.post_type,
    )
    db.add(post)
    await db.flush()

    return PostOut(
        id=str(post.id),
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        like_count=0,
        user_liked=False,
        author_id=str(current_user.id),
        author_name=current_user.full_name,
        can_delete=True,
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.put("/posts/{post_id}", response_model=PostOut)
async def update_post(
    post_id: str,
    payload: PostUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a post (author only)"""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Can only edit your own posts")

    if payload.title is not None:
        post.title = payload.title.strip()
    if payload.content is not None:
        post.content = payload.content.strip()
    if payload.is_active is not None:
        post.is_active = payload.is_active

    post.updated_at = datetime.utcnow()
    await db.flush()

    user_liked_result = await db.execute(
        select(PostLike).where(
            (PostLike.post_id == post.id) & (PostLike.user_id == current_user.id)
        )
    )
    user_liked = user_liked_result.scalar_one_or_none() is not None

    return PostOut(
        id=str(post.id),
        title=post.title,
        content=post.content,
        post_type=post.post_type,
        like_count=post.like_count,
        user_liked=user_liked,
        author_id=str(post.user_id),
        author_name=current_user.full_name,
        can_delete=(post.user_id == current_user.id or _is_super_admin(current_user)),
        created_at=post.created_at.isoformat(),
        updated_at=post.updated_at.isoformat(),
    )


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a post (author or super admin)"""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    if post.user_id != current_user.id and not _is_super_admin(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the post author or super admin can delete this post",
        )

    await db.delete(post)
    await db.commit()


@router.post("/posts/{post_id}/like")
async def like_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Like a post"""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    # Check if already liked
    existing_like = await db.execute(
        select(PostLike).where(
            (PostLike.post_id == post_id) & (PostLike.user_id == current_user.id)
        )
    )
    if existing_like.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already liked this post")

    like = PostLike(post_id=post_id, user_id=current_user.id)
    post.like_count = (post.like_count or 0) + 1
    db.add(like)
    await db.commit()

    return {"message": "Post liked", "like_count": post.like_count}


@router.post("/posts/{post_id}/unlike")
async def unlike_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Unlike a post"""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    like_result = await db.execute(
        select(PostLike).where(
            (PostLike.post_id == post_id) & (PostLike.user_id == current_user.id)
        )
    )
    like = like_result.scalar_one_or_none()

    if not like:
        raise HTTPException(status_code=400, detail="Not liked yet")

    post.like_count = max(0, (post.like_count or 1) - 1)
    await db.delete(like)
    await db.commit()

    return {"message": "Post unliked", "like_count": post.like_count}


@router.get("/posts/{post_id}/likes-count")
async def get_post_likes_count(
    post_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get likes count for a post"""
    result = await db.execute(select(CommunityPost).where(CommunityPost.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")

    return {"post_id": str(post_id), "like_count": post.like_count}
