"""
FastAPI routes — Embedding endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.db.models import Embedding as EmbeddingModel, Keyframe as KeyframeModel


router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.get("/{keyframe_id}")
async def get_embedding(
    keyframe_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get embedding for a keyframe."""
    result = await session.execute(
        select(EmbeddingModel).where(EmbeddingModel.keyframe_id == keyframe_id)
    )
    emb = result.scalar_one_or_none()
    if not emb:
        raise HTTPException(status_code=404, detail="Embedding not found")

    return {
        "id": str(emb.id),
        "keyframe_id": str(emb.keyframe_id),
        "model_name": emb.model_name,
        "dim": emb.dim,
        "has_mapped": emb.mapped_vector is not None,
    }


@router.get("/{keyframe_id}/vector")
async def get_embedding_vector(
    keyframe_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get the raw embedding vector for a keyframe."""
    result = await session.execute(
        select(EmbeddingModel).where(EmbeddingModel.keyframe_id == keyframe_id)
    )
    emb = result.scalar_one_or_none()
    if not emb:
        raise HTTPException(status_code=404, detail="Embedding not found")

    # Return the mapped vector if available, otherwise raw
    vector = emb.mapped_vector or emb.vector
    return {
        "keyframe_id": str(emb.keyframe_id),
        "vector": vector,
        "dim": emb.mapped_dim or emb.dim,
        "model_name": emb.model_name,
    }
