"""
FastAPI routes — Image & Video analysis endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.background import BackgroundTasks
from PIL import Image
import io

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
        # This means we skip the DINOv2→CLIP alignment step.
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

    embedder = get_embedder()
    aligner = get_or_initialize_aligner()
    all_axes = get_all_axes()
    reverser = get_prompt_reverser()

    # Step 1: DINOv2 embedding
    dinov2_emb = embedder.embed_pil_image(pil_image)

    # Step 2: Project to CLIP space
    if aligner.is_trained:
        aligned_emb = aligner.project(dinov2_emb)
    else:
        # MVP fallback: use CLIP image encoding directly (slightly less accurate)
        aligned_emb = aligner.encode_image(pil_image)

    # Step 3: Style axis projection
    scores = project_embedding(aligned_emb)
    by_category = project_by_category(aligned_emb)

    # Step 4: Prompt generation
    try:
        prompt_result = reverser.generate(scores)
        generated_prompt = prompt_result["prompt"]
        confidence = prompt_result.get("confidence")
    except Exception:
        generated_prompt = ", ".join(
            k.replace("_", " ") for k, v in sorted(scores.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        confidence = None

    # Step 5: Similar frame search
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
