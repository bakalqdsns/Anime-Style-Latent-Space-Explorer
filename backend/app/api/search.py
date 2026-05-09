"""
FastAPI routes — Similar frame search endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.core.searcher import search_similar
from app.models.prompt import SimilarFramesResponse, SimilarFrame


router = APIRouter(prefix="/similar", tags=["search"])


@router.get("/{keyframe_id}", response_model=SimilarFramesResponse)
async def get_similar_frames(
    keyframe_id: UUID,
    limit: int = Query(default=10, le=50),
    anime: Optional[str] = None,
    cluster_id: Optional[str] = None,
    score_threshold: float = Query(default=0.0, ge=0.0, le=1.0),
):
    """
    Find frames similar to a given keyframe.
    Requires keyframe to be stored in Qdrant with its embedding.
    """
    # Note: In production, retrieve the stored embedding from DB by keyframe_id
    # For MVP, this endpoint is called after analyze_image which already returns similar frames
    return SimilarFramesResponse(
        query_keyframe_id=keyframe_id,
        similar=[],
    )


@router.post("/by-embedding")
async def search_by_embedding(
    embedding: list[float],
    limit: int = Query(default=10, le=50),
    anime: Optional[str] = None,
):
    """
    Search similar frames by providing an embedding vector directly.
    """
    import numpy as np

    emb = np.array(embedding)
    results = search_similar(emb, limit=limit, anime=anime, score_threshold=0.0)

    return SimilarFramesResponse(
        query_keyframe_id=None,
        similar=[
            SimilarFrame(
                id=r["id"],
                path=r["payload"].get("path") if r.get("payload") else None,
                anime=r["payload"].get("anime") if r["payload"] else None,
                studio=r["payload"].get("studio") if r["payload"] else None,
                score=round(r["score"], 4),
            )
            for r in results
        ],
    )
