""""
FastAPI routes — Image & Video analysis endpoints.
"""
import traceback
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.background import BackgroundTasks
from PIL import Image
import io
import logging

logger = logging.getLogger("uvicorn.error")

from app.core.embedder import Embedder
from app.core.aligner import get_aligner
from app.core.style_axis import get_all_axes, project_embedding, project_by_category, initialize_style_axes
from app.core.searcher import search_similar
from app.core.prompt_reverser import get_prompt_reverser
from app.config import get_settings
from app.models.analyze import ImageAnalyzeResponse, SimilarFrameInResponse
from app.models.prompt import SimilarFramesResponse, SimilarFrame


router = APIRouter(prefix="/analyze", tags=["analyze"])
settings = get_settings()


# Lazy initialization on first use
_embedder: Optional[Embedder] = None


def get_embedder() -> Embedder:
    global _embedder
    if _embedder is None:
        _embedder = Embedder(
            model_name=settings.dinov2_model,
            cache_dir=settings.embedding_cache_dir,
            batch_size=32,
        )
    return _embedder


def get_or_initialize_aligner():
    aligner = get_aligner()
    if not aligner.is_trained:
        # In production, load trained W matrix. For MVP demo, use identity projection.
        # This means we skip the DINOv2->CLIP alignment step.
        # A trained W matrix needs ~100 labeled pairs to be loaded here.
        pass
    return aligner


@router.post("/image", response_model=ImageAnalyzeResponse)
async def analyze_image(file: UploadFile = File(...)):
    """
    Analyze a single uploaded image.
    Returns style axis scores, generated prompt, and similar frames.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be an image",
        )

    # Read image
    contents = await file.read()
    try:
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    # Ensure style axes are initialized
    try:
        initialize_style_axes()
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="Style axes not initialized. Run scripts/init_style_axes.py first.",
        )
    except Exception as e:
        logger.error(f"[analyze] initialize_style_axes FAILED:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize style axes: {e}",
        )

    # Step 1: DINOv2 embedding
    try:
        embedder = get_embedder()
        dinov2_emb = embedder.embed_pil_image(pil_image)
    except Exception as e:
        logger.error(f"[analyze] DINOv2 embedding FAILED:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compute image embedding: {e}",
        )

    # Step 2: Project to CLIP space
    try:
        aligner = get_or_initialize_aligner()
        if aligner.is_trained:
            aligned_emb = aligner.project(dinov2_emb)
        else:
            aligned_emb = aligner.encode_image(pil_image)
    except Exception as e:
        logger.error(f"[analyze] CLIP alignment FAILED:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to align embedding: {e}",
        )

    # Step 3: Style axis projection
    try:
        all_axes = get_all_axes()
        scores = project_embedding(aligned_emb)
        by_category = project_by_category(aligned_emb)
    except Exception as e:
        logger.error(f"[analyze] style axis projection FAILED:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to project onto style axes: {e}",
        )

    # Step 4: Prompt generation
    try:
        reverser = get_prompt_reverser()
        prompt_result = reverser.generate(scores)
        generated_prompt = prompt_result["prompt"]
        confidence = prompt_result.get("confidence")
    except Exception:
        logger.warning(f"[analyze] prompt generation FAILED, using fallback:\n{traceback.format_exc()}")
        generated_prompt = ", ".join(
            k.replace("_", " ") for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        confidence = None

    # Step 5: Similar frame search
    try:
        similar_raw = search_similar(aligned_emb, limit=5, score_threshold=0.3)
        similar_frames = [
            SimilarFrameInResponse(
                id=r["id"],
                path=r["payload"].get("path") if r.get("payload") else None,
                anime=r["payload"].get("anime") if r.get("payload") else None,
                score=round(r["score"], 4),
            )
            for r in similar_raw
        ]
    except Exception:
        similar_frames = []

    return ImageAnalyzeResponse(
        style_axes=scores,
        style_axes_by_category=by_category,
        generated_prompt=generated_prompt,
        confidence=confidence,
        similar_frames=similar_frames,
    )


@router.get("/health")
async def analyze_health():
    """Quick health check."""
    return {"status": "ok"}
