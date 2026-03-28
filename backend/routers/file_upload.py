"""
File upload routes
Handles secure file uploads with validation and object storage
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
import hashlib
import os
from typing import Optional

from database import get_db
from auth import get_current_user
from services import FileService
from models import User
from config import settings

router = APIRouter(prefix="/files", tags=["files"])


async def calculate_file_hash(file_content: bytes) -> str:
    """Calculate SHA-256 hash of file"""
    return hashlib.sha256(file_content).hexdigest()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    file_type: Optional[str] = "document",
    verification_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload file with validation and storage"""
    try:
        # Read file content
        contents = await file.read()
        file_size = len(contents)

        # Validate file
        service = FileService(db)
        await service.validate_file(file_size, file.content_type)

        # Calculate file hash
        file_hash = await calculate_file_hash(contents)

        # TODO: Upload to S3 or local storage
        # For now, store path reference
        filename = f"{current_user.id}/{file.filename}"
        file_url = f"/uploads/{filename}"

        # Create database record
        db_file = await service.create_file_record(
            user_id=str(current_user.id),
            filename=filename,
            file_type=file_type,
            mime_type=file.content_type,
            file_size=file_size,
            file_url=file_url,
            verification_id=verification_id,
        )

        # Store file hash in database
        db_file.file_hash = file_hash
        await db.commit()

        return {
            "id": str(db_file.id),
            "filename": file.filename,
            "file_type": file_type,
            "file_size": file_size,
            "mime_type": file.content_type,
            "file_hash": file_hash,
            "uploaded_at": db_file.uploaded_at.isoformat(),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File upload failed",
        )


@router.get("/list")
async def list_user_files(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of files uploaded by current user"""
    service = FileService(db)
    files = await service.get_user_files(str(current_user.id))

    return [
        {
            "id": str(f.id),
            "filename": f.original_filename,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "mime_type": f.mime_type,
            "uploaded_at": f.uploaded_at.isoformat(),
            "expires_at": f.expires_at.isoformat() if f.expires_at else None,
        }
        for f in files
    ]


@router.get("/download/{file_id}")
async def download_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download file (verification: user owns file)"""
    # TODO: Implement file download with ownership verification
    pass


@router.delete("/delete/{file_id}")
async def delete_file(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete uploaded file"""
    # TODO: Implement file deletion with ownership verification
    pass
