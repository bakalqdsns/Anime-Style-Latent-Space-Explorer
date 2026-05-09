"""
SQLAlchemy ORM models — mapped from schemas.sql
"""
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    ARRAY,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from app.db.database import Base


def _uuid() -> uuid.UUID:
    return uuid.uuid4()


def _now() -> datetime:
    return datetime.utcnow()


class Keyframe(Base):
    __tablename__ = "keyframes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    video_name: Mapped[Optional[str]] = mapped_column(String(256))
    anime: Mapped[Optional[str]] = mapped_column(String(256), index=True)
    studio: Mapped[Optional[str]] = mapped_column(String(256))
    director: Mapped[Optional[str]] = mapped_column(String(256))
    year: Mapped[Optional[int]] = mapped_column(Integer)
    timestamp: Mapped[Optional[float]] = mapped_column(Float)
    width: Mapped[Optional[int]] = mapped_column(Integer)
    height: Mapped[Optional[int]] = mapped_column(Integer)
    hash: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="keyframe", cascade="all, delete-orphan")
    projections: Mapped[list["StyleProjection"]] = relationship(back_populates="keyframe", cascade="all, delete-orphan")
    prompts: Mapped[list["Prompt"]] = relationship(back_populates="keyframe", cascade="all, delete-orphan")
    style_space: Mapped[Optional["StyleSpaceEmbedding"]] = relationship(back_populates="keyframe", uselist=False)


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    keyframe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("keyframes.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(64), nullable=False)
    vector: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    dim: Mapped[int] = mapped_column(Integer, nullable=False)
    mapped_vector: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float))
    mapped_dim: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    keyframe: Mapped["Keyframe"] = relationship(back_populates="embeddings")


class StyleAxis(Base):
    __tablename__ = "style_axes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    category: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    prompt_positive: Mapped[str] = mapped_column(Text, nullable=False)
    prompt_negative: Mapped[Optional[str]] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    direction_vector: Mapped[Optional[list[float]]] = mapped_column(ARRAY(Float))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    projections: Mapped[list["StyleProjection"]] = relationship(back_populates="axis")


class StyleProjection(Base):
    __tablename__ = "style_projections"
    __table_args__ = (
        UniqueConstraint("keyframe_id", "style_axis_id", name="uq_keyframe_axis"),
        Index("idx_projections_keyframe", "keyframe_id"),
        Index("idx_projections_axis", "style_axis_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    keyframe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("keyframes.id", ondelete="CASCADE"), nullable=False)
    style_axis_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("style_axes.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    keyframe: Mapped["Keyframe"] = relationship(back_populates="projections")
    axis: Mapped["StyleAxis"] = relationship(back_populates="projections")


class Cluster(Base):
    __tablename__ = "clusters"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[Optional[str]] = mapped_column(String(128))
    color: Mapped[Optional[str]] = mapped_column(String(8))
    centroid: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    size: Mapped[int] = mapped_column(Integer, default=0)
    representative_frame_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("keyframes.id"))
    params_hash: Mapped[Optional[str]] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class StyleSpaceEmbedding(Base):
    __tablename__ = "style_space_embeddings"

    keyframe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("keyframes.id", ondelete="CASCADE"), primary_key=True)
    umap_x: Mapped[float] = mapped_column(Float, nullable=False)
    umap_y: Mapped[float] = mapped_column(Float, nullable=False)
    umap_z: Mapped[Optional[float]] = mapped_column(Float)
    cluster_id: Mapped[Optional[uuid.UUID]] = mapped_column(Uuid, ForeignKey("clusters.id"))
    params_hash: Mapped[Optional[str]] = mapped_column(String(64))
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)

    keyframe: Mapped["Keyframe"] = relationship(back_populates="style_space")
    cluster: Mapped[Optional["Cluster"]] = relationship()


class Prompt(Base):
    __tablename__ = "prompts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    keyframe_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("keyframes.id", ondelete="CASCADE"), nullable=False)
    prompt_text: Mapped[str] = mapped_column(Text, nullable=False)
    style_axes_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    llm_provider: Mapped[Optional[str]] = mapped_column(String(32))
    confidence: Mapped[Optional[float]] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)

    keyframe: Mapped["Keyframe"] = relationship(back_populates="prompts")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    job_type: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending", index=True)
    params: Mapped[Optional[dict]] = mapped_column(JSON)
    result: Mapped[Optional[dict]] = mapped_column(JSON)
    error: Mapped[Optional[str]] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now, onupdate=_now)


class AlignerMatrix(Base):
    __tablename__ = "aligner_matrices"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    matrix: Mapped[list[float]] = mapped_column(ARRAY(Float), nullable=False)
    clip_model: Mapped[Optional[str]] = mapped_column(String(64))
    dinov2_model: Mapped[Optional[str]] = mapped_column(String(64))
    trained_samples: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
