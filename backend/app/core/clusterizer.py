"""
Style Space Clustering — UMAP dimensionality reduction + HDBSCAN clustering.

UMAP: 768D (CLIP-aligned) → 3D (for Three.js visualization)
HDBSCAN: density-based clustering in UMAP space
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import numpy as np
import umap
from sklearn.cluster import HDBSCAN

from app.config import get_settings


settings = get_settings()


class Clusterizer:
    """
    UMAP + HDBSCAN pipeline for style space analysis.
    """

    def __init__(
        self,
        n_neighbors: int | None = None,
        min_dist: float | None = None,
        hdbscan_min_cluster_size: int | None = None,
        hdbscan_min_samples: int | None = None,
    ):
        self.n_neighbors = n_neighbors or settings.umap_n_neighbors
        self.min_dist = min_dist or settings.umap_min_dist
        self.hdbscan_min_cluster_size = hdbscan_min_cluster_size or settings.hdbscan_min_cluster_size
        self.hdbscan_min_samples = hdbscan_min_samples or settings.hdbscan_min_samples
        self._reducer: Optional[umap.UMAP] = None
        self._hdbscan: Optional[HDBSCAN] = None
        self._centroids: Optional[dict[int, np.ndarray]] = None

    @property
    def params_hash(self) -> str:
        """Hash of current parameters for cache invalidation."""
        key = f"nn{self.n_neighbors}_md{self.min_dist}_mcs{self.hdbscan_min_cluster_size}_ms{self.hdbscan_min_samples}"
        return hashlib.md5(key.encode()).hexdigest()[:12]

    def fit_transform(self, embeddings: np.ndarray) -> np.ndarray:
        """
        Reduce embeddings from 768D to 3D using UMAP.
        Caches the reducer for subsequent calls.
        """
        if self._reducer is None:
            self._reducer = umap.UMAP(
                n_components=3,
                n_neighbors=self.n_neighbors,
                min_dist=self.min_dist,
                metric="cosine",
                random_state=42,
            )
        return self._reducer.fit_transform(embeddings)

    def fit_predict_clusters(self, umap_coords: np.ndarray) -> np.ndarray:
        """
        Run HDBSCAN on UMAP coordinates.
        Returns cluster labels (-1 = noise).
        """
        self._hdbscan = HDBSCAN(
            min_cluster_size=self.hdbscan_min_cluster_size,
            min_samples=self.hdbscan_min_samples,
            metric="cosine",
        )
        return self._hdbscan.fit_predict(umap_coords)

    def compute_centroids(
        self,
        umap_coords: np.ndarray,
        labels: np.ndarray,
    ) -> dict[int, np.ndarray]:
        """Compute cluster centroids (in UMAP 3D space)."""
        self._centroids = {}
        unique_labels = set(labels)
        for label in unique_labels:
            if label == -1:
                continue
            mask = labels == label
            self._centroids[label] = umap_coords[mask].mean(axis=0)
        return self._centroids

    def save(self, path: Path) -> None:
        """Save reducer + HDBSCAN config to disk."""
        data = {
            "params_hash": self.params_hash,
            "n_neighbors": self.n_neighbors,
            "min_dist": self.min_dist,
            "hdbscan_min_cluster_size": self.hdbscan_min_cluster_size,
            "hdbscan_min_samples": self.hdbscan_min_samples,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def load(self, path: Path) -> None:
        """Load reducer + HDBSCAN config."""
        with open(path) as f:
            data = json.load(f)
        self.n_neighbors = data["n_neighbors"]
        self.min_dist = data["min_dist"]
        self.hdbscan_min_cluster_size = data["hdbscan_min_cluster_size"]
        self.hdbscan_min_samples = data["hdbscan_min_samples"]


# Predefined cluster colors
CLUSTER_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4",
    "#FFEAA7", "#DDA0DD", "#98D8C8", "#F7DC6F",
    "#BB8FCE", "#85C1E9", "#F8B500", "#52B788",
    "#F06292", "#7E57C2", "#26C6DA", "#D4E157",
    "#FF7043", "#8D6E63", "#78909C", "#AED581",
]


def get_cluster_color(label: int) -> str:
    """Get a deterministic color for a cluster label."""
    if label == -1:
        return "#9E9E9E"  # Gray for noise
    return CLUSTER_COLORS[label % len(CLUSTER_COLORS)]
