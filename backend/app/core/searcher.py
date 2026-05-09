"""
Similar frame search — Qdrant vector similarity search with filters.
"""
from __future__ import annotations

from typing import Optional
from uuid import UUID

import numpy as np

from app.vector.qdrant import get_vector_store


def search_similar(
    query_embedding: np.ndarray,
    limit: int = 10,
    anime: str | None = None,
    cluster_id: str | None = None,
    score_threshold: float = 0.0,
) -> list[dict]:
    """
    Search for similar frames using Qdrant.

    Args:
        query_embedding: CLIP-aligned 768D embedding
        limit: max results
        anime: filter by anime name
        cluster_id: filter by cluster
        score_threshold: minimum cosine similarity

    Returns list of {id, score, payload} dicts.
    """
    store = get_vector_store()
    return store.search(
        query_vector=query_embedding,
        limit=limit,
        anime=anime,
        cluster_id=cluster_id,
        score_threshold=score_threshold,
    )


def index_keyframe(
    keyframe_id: UUID | str,
    embedding: np.ndarray,
    payload: dict,
    dim: int = 768,
) -> None:
    """Index a keyframe embedding in Qdrant."""
    store = get_vector_store()
    kid = str(keyframe_id)
    store.upsert(keyframe_id=kid, vector=embedding, payload=payload, dim=dim)
