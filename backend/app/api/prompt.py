"""
FastAPI routes — Prompt generation endpoints.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_session
from app.db.models import Keyframe as KeyframeModel, StyleProjection, Prompt as PromptModel, StyleAxis as StyleAxisModel
from app.core.prompt_reverser import get_prompt_reverser
from app.models.prompt import PromptGenerateRequest, PromptGenerateResponse


router = APIRouter(prefix="/prompt", tags=["prompt"])


@router.post("/generate", response_model=PromptGenerateResponse)
async def generate_prompt(
    request: PromptGenerateRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Generate a prompt from style axis scores.
    Provide either keyframe_id (load scores from DB) or style_axes directly.
    """
    style_axes: dict[str, float]

    if request.keyframe_id:
        result = await session.execute(
            select(StyleProjection).where(
                StyleProjection.keyframe_id == request.keyframe_id
            )
        )
        projections = result.scalars().all()
        if not projections:
            raise HTTPException(status_code=404, detail="No style projections found for this keyframe.")

        axis_ids = [p.style_axis_id for p in projections]
        axes_result = await session.execute(
            select(StyleAxisModel).where(StyleAxisModel.id.in_(axis_ids))
        )
        axes_map = {ax.id: ax.name for ax in axes_result.scalars().all()}
        style_axes = {axes_map[p.style_axis_id]: p.score for p in projections}

    elif request.style_axes:
        style_axes = request.style_axes
    else:
        raise HTTPException(status_code=400, detail="Provide either keyframe_id or style_axes.")

    reverser = get_prompt_reverser()
    result = reverser.generate(style_axes, max_words=request.max_words)

    return PromptGenerateResponse(
        prompt=result["prompt"],
        confidence=result.get("confidence"),
        llm_provider=result.get("provider", "unknown"),
        style_axes_used=style_axes,
    )
