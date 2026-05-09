"""Pydantic request/response models — Analyze (Image & Video)"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ImageAnalyzeRequest(BaseModel):
    pass  # image is sent as file upload, not JSON body


class ImageAnalyzeResponse(BaseModel):
    keyframe_id: Optional[UUID] = None
    style_axes: dict[str, float]
    style_axes_by_category: dict[str, dict[str, float]]
    generated_prompt: str
    confidence: Optional[float] = None
    similar_frames: list["SimilarFrameInResponse"] = []


class SimilarFrameInResponse(BaseModel):
    id: UUID
    path: Optional[str] = None
    anime: Optional[str] = None
    score: float


class AnalyzeError(BaseModel):
    detail: str
