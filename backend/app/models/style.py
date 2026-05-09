"""Pydantic request/response models — Style Axes & Projections"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class StyleAxisBase(BaseModel):
    category: str
    name: str
    prompt_positive: str
    prompt_negative: Optional[str] = None
    description: Optional[str] = None


class StyleAxisCreate(StyleAxisBase):
    pass


class StyleAxisRead(StyleAxisBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class StyleAxisListResponse(BaseModel):
    axes: list[StyleAxisRead]
    categories: list[str]


class StyleProjectionRead(BaseModel):
    id: UUID
    keyframe_id: UUID
    style_axis_id: UUID
    axis_name: str
    axis_category: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class StyleProjectionsResponse(BaseModel):
    keyframe_id: UUID
    projections: dict[str, float]  # {axis_name: score}
    categories: dict[str, dict[str, float]]  # {category: {axis_name: score}}


class StyleSpaceFrame(BaseModel):
    id: UUID
    x: float
    y: float
    z: Optional[float] = None
    anime: Optional[str] = None
    studio: Optional[str] = None
    cluster_id: Optional[UUID] = None
    cluster_color: Optional[str] = None
    path: Optional[str] = None


class StyleSpaceCluster(BaseModel):
    id: UUID
    name: Optional[str] = None
    color: Optional[str] = None
    size: int
    representative_frame_id: Optional[UUID] = None


class StyleSpaceResponse(BaseModel):
    frames: list[StyleSpaceFrame]
    clusters: list[StyleSpaceCluster]
    total: int
