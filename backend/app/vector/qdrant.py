"""
Qdrant vector database wrapper.
"""
from __future__ import annotations

from typing import Optional

import numpy as np
import qdrant_client
from qdrant_client.http import models as qmodels

from app.config import get_settings


settings = get_settings()


class VectorStore:
    """Qdrant wrapper with graceful fallback when unavailable."""

    def __init__(self, collection_name: str = "keyframes"):
        self.collection_name = collection_name
        self._client: Optional[qdrant_client.QdrantClient] = None
        self._available = False
        self._init_client()

    def _init_client(self) -> None:
        try:
            self._client = qdrant_client.QdrantClient(
                url=settings.qdrant_url,
                timeout=5.0,
            )
            self._client.get_collections()
            self._available = True
        except Exception:
            self._client = None
            self._available = False

    @property
    def is_available(self) -> bool:
        return self._available

    def _ensure_collection(self, dim: int) -> None:
        if not self._client:
            return
        try:
            collections = self._client.get_collections().collections
            names = [c.name for c in collections]
            if self.collection_name not in names:
                self._client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=qmodels.VectorParams(
                        size=dim,
                        distance=qmodels.Distance.COSINE,
                    ),
                )
                for field, schema in [
                    ("anime", qmodels.PayloadSchemaType.KEYWORD),
                    ("studio", qmodels.PayloadSchemaType.KEYWORD),
                    ("keyframe_id", qmodels.PayloadSchemaType.KEYWORD),
                    ("cluster_id", qmodels.PayloadSchemaType.KEYWORD),
                ]:
                    try:
                        self._client.create_payload_index(
                            self.collection_name,
                            field_name=field,
                            field_schema=schema,
                        )
                    except Exception:
                        pass
        except Exception as e:
            raise RuntimeError(f"Failed to create Qdrant collection: {e}")

    def upsert(
        self,
        keyframe_id: str,
        vector: np.ndarray,
        payload: dict,
        dim: int = 768,
    ) -> None:
        """Insert or update a vector."""
        if not self._client:
            return
        self._ensure_collection(dim)
        self._client.upsert(
            collection_name=self.collection_name,
            points=[
                qmodels.PointStruct(
                    id=keyframe_id,
                    vector=vector.tolist(),
                    payload={"keyframe_id": keyframe_id, **payload},
                )
            ],
        )

    def search(
        self,
        query_vector: np.ndarray,
        limit: int = 10,
        anime: str | None = None,
        cluster_id: str | None = None,
        score_threshold: float | None = None,
    ) -> list[dict]:
        """Search similar vectors with optional filters."""
        if not self._client:
            return []

        must_conditions = []
        if anime:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="anime",
                    match=qmodels.MatchValue(value=anime),
                )
            )
        if cluster_id:
            must_conditions.append(
                qmodels.FieldCondition(
                    key="cluster_id",
                    match=qmodels.MatchValue(value=cluster_id),
                )
            )

        query_filter = qmodels.Filter(must=must_conditions) if must_conditions else None

        try:
            results = self._client.search(
                collection_name=self.collection_name,
                query_vector=query_vector.tolist(),
                limit=limit,
                query_filter=query_filter,
                score_threshold=score_threshold,
            )
        except Exception:
            return []

        return [{"id": r.id, "score": r.score, "payload": r.payload} for r in results]

    def count(self) -> int:
        if not self._client:
            return 0
        try:
            info = self._client.get_collection(self.collection_name)
            return info.points_count
        except Exception:
            return 0

    def delete(self, keyframe_id: str) -> None:
        if not self._client:
            return
        try:
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=qmodels.PointIdsList(points=[keyframe_id]),
            )
        except Exception:
            pass

    def clear(self) -> None:
        if not self._client:
            return
        try:
            self._client.delete_collection(self.collection_name)
        except Exception:
            pass


_vector_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStore(collection_name=settings.qdrant_collection)
    return _vector_store
