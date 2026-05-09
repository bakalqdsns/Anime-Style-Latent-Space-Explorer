"""Pydantic request/response models — Prompt Generation"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PromptGenerateRequest(BaseModel):
    keyframe_id: Optional[UUID] = None
    style_axes: Optional[dict[str, float]] = None
    max_words: int = Field(default=50, le=100)


class PromptGenerateResponse(BaseModel):
    prompt: str
    confidence: Optional[float] = None
    llm_provider: str
    style_axes_used: Optional[dict[str, float]] = None


class PromptRead(BaseModel):
    id: UUID
    keyframe_id: UUID
    prompt_text: str
    style_axes_snapshot: Optional[dict] = None
    llm_provider: Optional[str] = None
    confidence: Optional[float] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SimilarFramesResponse(BaseModel):
    query_keyframe_id: Optional[UUID] = None
    similar: list["SimilarFrame"]


class SimilarFrame(BaseModel):
    id: UUID
    path: Optional[str] = None
    anime: Optional[str] = None
    studio: Optional[str] = None
    score: float
    style_axes: Optional[dict[str, float]] = None
