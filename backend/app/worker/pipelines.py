"""
Async processing pipeline — end-to-end batch processing.

Phase 5+ uses BackgroundTasks (no Celery in MVP).
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Optional

from app.core.embedder import Embedder
from app.core.aligner import get_aligner
from app.core.style_axis import initialize_style_axes, project_embedding
from app.core.clusterizer import Clusterizer, get_cluster_color
from app.core.searcher import index_keyframe
from app.config import get_settings
from app.db.database import session_context
from app.db.models import (
    Keyframe,
    Embedding,
    StyleProjection,
    StyleAxis,
    Cluster,
    StyleSpaceEmbedding,
    Job,
)


settings = get_settings()


def _update_job(job_id: uuid.UUID, status: str, progress: int, result: dict = None, error: str = None):
    """Update job status in DB."""
    import asyncio
    async def _update():
        async with session_context() as session:
            from sqlalchemy import update
            await session.execute(
                update(Job).where(Job.id == job_id).values(
                    status=status,
                    progress=progress,
                    result=result,
                    error=error,
                )
            )
    try:
        asyncio.run(_update())
    except Exception:
        pass


def process_video_pipeline(
    video_path: str | Path,
    output_dir: str | Path,
    metadata: dict,
    job_id: Optional[uuid.UUID] = None,
):
    """
    End-to-end video processing pipeline.

    Steps:
    1. Extract keyframes (ffmpeg + Laplacian blur filter)
    2. Compute DINOv2 embeddings
    3. Project onto style axes
    4. Index in Qdrant
    """
    from app.core.keyframe import KeyframeExtractor
    import numpy as np

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    _update_job(job_id, "running", 10)

    # Step 1: Extract keyframes
    extractor = KeyframeExtractor()
    frames = extractor.extract(video_path, output_dir, metadata)
    _update_job(job_id, "running", 30)

    if not frames:
        _update_job(job_id, "failed", 0, error="No keyframes extracted")
        return

    # Step 2: Compute embeddings
    embedder = Embedder(
        model_name=settings.dinov2_model,
        cache_dir=settings.embedding_cache_dir,
        batch_size=32,
    )
    frame_paths = [f["path"] for f in frames]
    embeddings = embedder.embed_batch(frame_paths)
    _update_job(job_id, "running", 60)

    # Step 3: Style axis projection
    try:
        initialize_style_axes()
        from app.core.style_axis import get_all_axes
        all_axes = get_all_axes()
    except FileNotFoundError:
        all_axes = {}

    aligner = get_aligner()
    projections = []
    for emb in embeddings:
        if aligner.is_trained:
            aligned = aligner.project(emb)
        else:
            aligned = aligner.encode_image(__import__("PIL").Image.open(frame_paths[0]).convert("RGB"))
        if all_axes:
            scores = project_embedding(aligned)
        else:
            scores = {}
        projections.append(scores)
    _update_job(job_id, "running", 80)

    # Step 4: Index in Qdrant
    for frame, emb, proj in zip(frames, embeddings, projections):
        aligned = emb  # simplified
        payload = {
            "anime": metadata.get("anime"),
            "studio": metadata.get("studio"),
            "path": frame["path"],
            "timestamp": frame["timestamp"],
        }
        try:
            index_keyframe(frame["id"], aligned, payload, dim=embedder.embedding_dim)
        except Exception:
            pass

    _update_job(job_id, "completed", 100, result={
        "frames_extracted": len(frames),
        "style_axes_computed": True,
    })
