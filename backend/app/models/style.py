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
    id: Optional[UUID] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StyleAxisListResponse(BaseModel):
    axes: list[StyleAxisRead]
    categories: list[str]


class StyleProjectionRead(BaseModel):
    id: str
    keyframe_id: str
    style_axis_id: str
    axis_name: str
    axis_category: str
    score: float
    created_at: datetime

    class Config:
        from_attributes = True


class StyleProjectionsResponse(BaseModel):
    keyframe_id: str
    projections: dict[str, float]
    categories: dict[str, dict[str, float]]


class StyleSpaceFrame(BaseModel):
    id: str
    x: float
    y: float
    z: Optional[float] = None
    anime: Optional[str] = None
    studio: Optional[str] = None
    cluster_id: Optional[str] = None
    cluster_color: Optional[str] = None
    path: Optional[str] = None


class StyleSpaceCluster(BaseModel):
    id: str
    name: Optional[str] = None
    color: Optional[str] = None
    size: int
    representative_frame_id: Optional[str] = None


class StyleSpaceResponse(BaseModel):
    frames: list[StyleSpaceFrame]
    clusters: list[StyleSpaceCluster]
    total: int
