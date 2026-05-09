"""Pydantic request/response models — Frame & Keyframe"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class KeyframeBase(BaseModel):
    path: str
    video_name: Optional[str] = None
    anime: Optional[str] = None
    studio: Optional[str] = None
    director: Optional[str] = None
    year: Optional[int] = None
    timestamp: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    hash: Optional[str] = None


class KeyframeCreate(KeyframeBase):
    pass


class KeyframeRead(KeyframeBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class KeyframeWithEmbedding(KeyframeRead):
    embedding: Optional["EmbeddingRead"] = None
    projections: Optional[list["StyleProjectionRead"]] = None
    prompt: Optional["PromptRead"] = None


class EmbeddingRead(BaseModel):
    id: UUID
    model_name: str
    dim: int
    created_at: datetime

    class Config:
        from_attributes = True


class VideoAnalysisRequest(BaseModel):
    anime: str
    studio: Optional[str] = None
    director: Optional[str] = None
    year: Optional[int] = None


class VideoAnalysisResponse(BaseModel):
    job_id: UUID
    status: str
    status_url: str


class VideoAnalysisStatus(BaseModel):
    job_id: UUID
    status: str
    progress: int = 0
    frames_extracted: int = 0
    style_axes_means: Optional[dict[str, float]] = None
    error: Optional[str] = None


# Lazy forward reference resolution
KeyframeWithEmbedding.model_rebuild()
