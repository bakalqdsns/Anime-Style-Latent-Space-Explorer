"""
FastAPI routes — Frame endpoints.
"""
import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Optional
from uuid import UUID

import os
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.db.models import Keyframe as KeyframeModel
from app.core.embedder import Embedder
from app.core.searcher import index_keyframe
from app.config import get_settings


settings = get_settings()

# Thread pool for blocking ML/IO operations
_executor = ThreadPoolExecutor(max_workers=4)

# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class FrameMetadata(BaseModel):
    anime: Optional[str] = None
    studio: Optional[str] = None
    director: Optional[str] = None
    year: Optional[int] = None
    bangumi_id: Optional[int] = None
    cover_url: Optional[str] = None


class BatchIndexRequest(BaseModel):
    frames: list[str]                       # absolute paths to image files
    anime: str
    episode: int = 1
    metadata: Optional[FrameMetadata] = None


class BatchIndexResult(BaseModel):
    indexed: int          # number of frames successfully indexed
    failed: int           # number of frames that failed
    errors: list[dict]    # per-frame error details


# ─────────────────────────────────────────────────────────────────────────────
# Router
# ─────────────────────────────────────────────────────────────────────────────

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

    if not os.path.exists(keyframe.path):
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(keyframe.path)


# ─────────────────────────────────────────────────────────────────────────────
# Batch index endpoint — called by Anime Batch Import Tool
# ─────────────────────────────────────────────────────────────────────────────

def _run_batch_index(frames: list[str], anime: str, episode: int, meta_dict: dict) -> BatchIndexResult:
    """
    Synchronous implementation of batch indexing.
    Runs in a thread pool to avoid blocking the FastAPI event loop.
    """
    settings_local = get_settings()
    embedder = Embedder(
        model_name=settings_local.dinov2_model,
        cache_dir=settings_local.embedding_cache_dir,
        batch_size=32,
    )
    # meta_dict is already a dict, already defaulted in handler


    indexed_count = 0
    failed_count = 0
    errors = []

    for frame_path in frames:
        try:
            emb = embedder.embed_image(frame_path)
            kid = str(uuid.uuid4())
            payload = {
                "anime": anime,
                "studio": meta_dict.get("studio"),
                "director": meta_dict.get("director"),
                "year": meta_dict.get("year"),
                "path": frame_path,
                "timestamp": f"ep{episode}",
            }
            index_keyframe(kid, emb, payload, dim=embedder.embedding_dim)
            indexed_count += 1
        except Exception as exc:
            failed_count += 1
            errors.append({"path": frame_path, "error": str(exc)})

    return BatchIndexResult(indexed=indexed_count, failed=failed_count, errors=errors)


@router.post("/batch-index", response_model=BatchIndexResult)
async def batch_index_frames(req: BatchIndexRequest):
    """
    Receive a list of extracted keyframe image paths, compute DINOv2 embeddings,
    and index them into Qdrant.

    Request body (matches Anime Batch Import Tool):
      {
        "frames": ["/absolute/path/to/frame_0001.jpg", ...],
        "anime": "番剧名称",
        "episode": 1,
        "metadata": {
          "anime": "番剧名称",
          "studio": "制作公司",
          "director": "导演",
          "year": 2024,
          "bangumi_id": 12345,
          "cover_url": "https://..."
        }
      }

    Response:
      { "indexed": N, "failed": M, "errors": [...] }
    """
    if not req.frames:
        raise HTTPException(status_code=400, detail="frames list cannot be empty")

    meta_dict = req.metadata.model_dump() if req.metadata else {}

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        _executor,
        _run_batch_index,
        req.frames,
        req.anime,
        req.episode,
        meta_dict,
    )
    return result
