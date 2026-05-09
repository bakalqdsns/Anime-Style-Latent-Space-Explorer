"""
FastAPI routes — Style axis endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.db.models import StyleAxis as StyleAxisModel
from app.core.style_axis import (
    get_all_axes,
    get_categories,
    project_embedding,
    project_by_category,
    initialize_style_axes,
)
from app.models.style import (
    StyleAxisListResponse,
    StyleAxisRead,
    StyleProjectionsResponse,
    StyleSpaceResponse,
    StyleSpaceFrame,
    StyleSpaceCluster,
)
from app.vector.qdrant import get_vector_store


router = APIRouter(prefix="/style", tags=["style"])


@router.get("/axes", response_model=StyleAxisListResponse)
async def list_axes():
    """List all 21 style axes grouped by category."""
    try:
        initialize_style_axes()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Style axes not initialized.")

    axes = get_all_axes()
    categories = get_categories()

    return StyleAxisListResponse(
        axes=[
            StyleAxisRead(
                id="",  # Will be filled from DB if needed
                category=ax.category,
                name=ax.name,
                prompt_positive=ax.prompt_positive,
                prompt_negative=ax.prompt_negative,
                description=ax.description,
                created_at=None,
            )
            for ax in axes.values()
        ],
        categories=categories,
    )


@router.post("/project")
async def project_single(
    embedding: list[float],
    aligned: bool = False,
):
    """
    Project a raw embedding onto all style axes.
    For debugging / testing without a full image upload.
    """
    import numpy as np

    try:
        initialize_style_axes()
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Style axes not initialized.")

    emb = np.array(embedding)
    if aligned:
        scores = project_embedding(emb)
    else:
        # If not aligned, just return zeros
        scores = {name: 0.0 for name in get_all_axes().keys()}

    by_category = project_by_category(emb) if aligned else {}
    return {"scores": scores, "by_category": by_category}


@router.get("/space", response_model=StyleSpaceResponse)
async def get_style_space(
    anime: Optional[str] = None,
    cluster_id: Optional[str] = None,
    limit: int = 1000,
):
    """
    Get the full style space for visualization.
    Returns all frame positions in 3D UMAP space.
    """
    store = get_vector_store()

    # Search with no vector = return all (Qdrant scroll)
    # For now, return empty if Qdrant has no data
    frames: list[StyleSpaceFrame] = []
    clusters: list[StyleSpaceCluster] = []

    if store.is_available:
        # Use scroll to get all points
        try:
            results, _ = store._client.scroll(
                collection_name=store.collection_name,
                limit=limit,
                with_vectors=False,
            )
            for r in results:
                payload = r.payload or {}
                frames.append(StyleSpaceFrame(
                    id=payload.get("keyframe_id", str(r.id)),
                    x=payload.get("umap_x", 0.0),
                    y=payload.get("umap_y", 0.0),
                    z=payload.get("umap_z", 0.0),
                    anime=payload.get("anime"),
                    studio=payload.get("studio"),
                    cluster_id=payload.get("cluster_id"),
                    cluster_color=payload.get("cluster_color"),
                    path=payload.get("path"),
                ))
        except Exception:
            pass

    return StyleSpaceResponse(frames=frames, clusters=clusters, total=len(frames))
