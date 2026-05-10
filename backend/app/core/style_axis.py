"""
Style Axis System — 21 predefined semantic style axes.

Each axis has:
  - category: COLOR / LIGHTING / COMPOSITION / DIRECTING
  - name: unique identifier
  - prompt_positive: CLIP text for the positive pole
  - prompt_negative: CLIP text for the negative pole (optional)
  - direction_vector: normalized CLIP direction vector (768D)
  - score: cosine similarity between projected image and direction
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

from app.config import get_settings
from app.core.aligner import get_aligner


settings = get_settings()


class StyleAxisDefinition(BaseModel):
    category: str
    name: str
    prompt_positive: str
    prompt_negative: Optional[str] = None
    description: Optional[str] = None


class StyleAxis:
    """Runtime style axis with precomputed direction vector."""

    def __init__(self, definition: StyleAxisDefinition, direction_vector: np.ndarray):
        self.category = definition.category
        self.name = definition.name
        self.prompt_positive = definition.prompt_positive
        self.prompt_negative = definition.prompt_negative
        self.description = definition.description
        self.direction_vector = direction_vector  # 768D, L2 normalized

    def project(self, aligned_embedding: np.ndarray) -> float:
        """Compute cosine similarity between aligned embedding and axis direction."""
        return float(np.dot(aligned_embedding, self.direction_vector))


_axis_registry: dict[str, StyleAxis] = {}
_axis_definitions: list[StyleAxisDefinition] = []
_categories: list[str] = []


def _load_definitions() -> list[StyleAxisDefinition]:
    global _axis_definitions, _categories
    if _axis_definitions:
        return _axis_definitions

    config_path = settings.style_axes_config
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            data = json.load(f)
        _axis_definitions = [StyleAxisDefinition(**ax) for ax in data["axes"]]
    else:
        raise FileNotFoundError(
            f"Style axes config not found at {config_path}. "
            "Make sure data/style_axes.json exists."
        )

    _categories = sorted(set(ax.category for ax in _axis_definitions))
    return _axis_definitions


def initialize_style_axes(
    cache_dir: Path | None = None,
    force_recompute: bool = False,
) -> dict[str, StyleAxis]:
    """Initialize all 21 style axes by computing CLIP direction vectors."""
    global _axis_registry

    if _axis_registry and not force_recompute:
        return _axis_registry

    definitions = _load_definitions()
    aligner = get_aligner()

    pos_texts = [d.prompt_positive for d in definitions]
    neg_texts = [d.prompt_negative or "" for d in definitions]

    cache_dir_ = cache_dir or settings.axis_cache_dir
    cache_path = cache_dir_ / "direction_vectors.npy"
    direction_vectors: Optional[np.ndarray] = None

    if cache_path.exists() and not force_recompute:
        try:
            cached = np.load(cache_path)
            if cached.shape[0] == len(definitions):
                direction_vectors = cached
        except Exception:
            pass

    if direction_vectors is None:
        try:
            pos_emb = aligner.encode_text(pos_texts)  # (N, 768)
        except Exception as e:
            raise RuntimeError(
                f"Failed to encode positive prompts with CLIP. "
                f"Make sure CLIP model is downloaded: {e}"
            )

        neg_emb_list = []
        for neg_text in neg_texts:
            if neg_text.strip():
                try:
                    neg_emb_list.append(aligner.encode_text(neg_text.strip()).squeeze())
                except Exception:
                    neg_emb_list.append(np.zeros(aligner.clip_dim))
            else:
                neg_emb_list.append(np.zeros(aligner.clip_dim))

        neg_emb = np.stack(neg_emb_list)  # (N, 768)
        direction = pos_emb - neg_emb
        norms = np.linalg.norm(direction, axis=1, keepdims=True)
        direction_vectors = direction / (norms + 1e-8)

        cache_dir_.mkdir(parents=True, exist_ok=True)
        np.save(cache_path, direction_vectors)

    _axis_registry = {}
    for i, definition in enumerate(definitions):
        _axis_registry[definition.name] = StyleAxis(definition, direction_vectors[i])

    return _axis_registry


def get_all_axes() -> dict[str, StyleAxis]:
    if not _axis_registry:
        initialize_style_axes()
    return _axis_registry


def get_axes_by_category(category: str) -> dict[str, StyleAxis]:
    all_axes = get_all_axes()
    return {name: ax for name, ax in all_axes.items() if ax.category == category}


def get_categories() -> list[str]:
    _load_definitions()
    return _categories


def project_embedding(aligned_embedding: np.ndarray) -> dict[str, float]:
    """Project an aligned embedding onto all style axes."""
    all_axes = get_all_axes()
    return {name: ax.project(aligned_embedding) for name, ax in all_axes.items()}


def project_by_category(aligned_embedding: np.ndarray) -> dict[str, dict[str, float]]:
    """Project and group results by category."""
    all_axes = get_all_axes()
    result: dict[str, dict[str, float]] = {}
    for name, ax in all_axes.items():
        if ax.category not in result:
            result[ax.category] = {}
        result[ax.category][name] = ax.project(aligned_embedding)
    return result
