"""Pydantic request/response models — Embedding"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class EmbeddingComputeRequest(BaseModel):
    keyframe_ids: list[UUID]
    model_name: str = "dinov2-vitl14"


class EmbeddingComputeResponse(BaseModel):
    job_id: UUID
    status: str


class EmbeddingRead(BaseModel):
    id: UUID
    keyframe_id: UUID
    model_name: str
    dim: int
    has_mapped: bool = False
    created_at: datetime

    class Config:
        from_attributes = True
