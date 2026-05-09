"""
FastAPI routes — Frame endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.db.models import Keyframe as KeyframeModel


router = APIRouter(prefix="/frames", tags=["frames"])


@router.get("/{keyframe_id}")
async def get_keyframe(
    keyframe_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get keyframe metadata by ID."""
    result = await session.execute(
        select(KeyframeModel).where(KeyframeModel.id == keyframe_id)
    )
    keyframe = result.scalar_one_or_none()
    if not keyframe:
        raise HTTPException(status_code=404, detail="Keyframe not found")

    return {
        "id": str(keyframe.id),
        "path": keyframe.path,
        "anime": keyframe.anime,
        "studio": keyframe.studio,
        "director": keyframe.director,
        "year": keyframe.year,
        "timestamp": keyframe.timestamp,
        "width": keyframe.width,
        "height": keyframe.height,
    }


@router.get("/{keyframe_id}/image")
async def get_keyframe_image(
    keyframe_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Serve the keyframe image file."""
    result = await session.execute(
        select(KeyframeModel).where(KeyframeModel.id == keyframe_id)
    )
    keyframe = result.scalar_one_or_none()
    if not keyframe:
        raise HTTPException(status_code=404, detail="Keyframe not found")

    import os
    if not os.path.exists(keyframe.path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(keyframe.path)
