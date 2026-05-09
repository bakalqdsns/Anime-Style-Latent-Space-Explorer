"""
CLIP text-image alignment module.

Aligns DINOv2 visual space (1024D) to CLIP text space (768D) via a linear mapping W.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor


class CLIPAligner:
    """
    CLIP alignment layer:
    DINOv2 (1024D) → Linear W (1024×768) → CLIP-aligned (768D)

    Training requires ~100 labeled (DINOv2_embedding, CLIP_text_embedding) pairs.
    """

    def __init__(
        self,
        clip_model_name: str = "openai/clip-vit-large-patch14",
        dinov2_dim: int = 1024,
        clip_dim: int = 768,
        device: str | None = None,
    ):
        self.clip_model_name = clip_model_name
        self.dinov2_dim = dinov2_dim
        self.clip_dim = clip_dim
        self._device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        self._clip_model: Optional[CLIPModel] = None
        self._clip_processor: Optional[CLIPProcessor] = None
        self._W: Optional[np.ndarray] = None

    def _load_clip(self) -> tuple[CLIPModel, CLIPProcessor]:
        if self._clip_model is None:
            self._clip_processor = CLIPProcessor.from_pretrained(self.clip_model_name)
            self._clip_model = CLIPModel.from_pretrained(self.clip_model_name)
            self._clip_model.to(self._device)
            self._clip_model.eval()
        return self._clip_model, self._clip_processor

    @property
    def W(self) -> Optional[np.ndarray]:
        return self._W

    @property
    def is_trained(self) -> bool:
        return self._W is not None

    def encode_text(self, texts: str | list[str]) -> np.ndarray:
        """Encode text(s) with CLIP, returns (N, 768) array."""
        model, processor = self._load_clip()
        if isinstance(texts, str):
            texts = [texts]

        with torch.no_grad():
            inputs = processor(text=texts, return_tensors="pt", padding=True, truncation=True)
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            embeddings = model.get_text_features(**inputs).cpu().numpy()

        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / (norms + 1e-8)

    def encode_image(self, image: Image.Image) -> np.ndarray:
        """Encode a PIL Image with CLIP, returns 768-dim vector."""
        model, processor = self._load_clip()

        with torch.no_grad():
            inputs = processor(images=image, return_tensors="pt")
            inputs = {k: v.to(self._device) for k, v in inputs.items()}
            embedding = model.get_image_features(**inputs).cpu().numpy().squeeze()

        embedding = embedding / (np.linalg.norm(embedding) + 1e-8)
        return embedding

    def compute_direction_vectors(
        self,
        prompts_positive: list[str],
        prompts_negative: list[str] | None = None,
    ) -> np.ndarray:
        """Compute direction vectors for style axes."""
        pos_emb = self.encode_text(prompts_positive)
        if prompts_negative:
            neg_emb = self.encode_text(prompts_negative)
            direction = pos_emb - neg_emb
        else:
            direction = pos_emb

        norms = np.linalg.norm(direction, axis=1, keepdims=True)
        return direction / (norms + 1e-8)

    def project(self, dinov2_embedding: np.ndarray, normalize: bool = True) -> np.ndarray:
        """
        Project DINOv2 embedding through learned W matrix to CLIP-aligned space.
        """
        if self._W is None:
            raise RuntimeError("Aligner W matrix not trained. Call train() or load() first.")

        is_single = dinov2_embedding.ndim == 1
        if is_single:
            dinov2_embedding = dinov2_embedding[np.newaxis, :]

        aligned = dinov2_embedding @ self._W

        if normalize:
            norms = np.linalg.norm(aligned, axis=1, keepdims=True)
            aligned = aligned / (norms + 1e-8)

        return aligned.squeeze() if is_single else aligned

    def train(
        self,
        X: np.ndarray,
        Y: np.ndarray,
        alpha: float = 1.0,
    ) -> dict:
        """
        Train linear mapping W via Ridge Regression (closed-form).
        W = Y.T @ X @ (X.T @ X + alpha * I)^-1

        Args:
            X: DINOv2 embeddings for training samples (N, 1024)
            Y: CLIP text embeddings for the same samples (N, 768)
            alpha: Ridge regularization strength

        Returns training metrics dict.
        """
        n = X.shape[0]
        XTX = X.T @ X + alpha * np.eye(self.dinov2_dim)
        XTY = X.T @ Y
        W = np.linalg.solve(XTX, XTY).T  # (768, 1024)

        Y_pred = X @ W.T
        ss_res = np.sum((Y - Y_pred) ** 2)
        ss_tot = np.sum((Y - Y.mean(axis=0)) ** 2)
        r2 = 1 - ss_res / (ss_tot + 1e-8)

        X_norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-8)
        Y_norm = Y / (np.linalg.norm(Y, axis=1, keepdims=True) + 1e-8)
        aligned = X_norm @ W.T
        aligned = aligned / (np.linalg.norm(aligned, axis=1, keepdims=True) + 1e-8)
        cosine_sim = np.mean(np.sum(aligned * Y_norm, axis=1))

        self._W = W

        return {
            "n_samples": n,
            "r2_score": float(r2),
            "mean_cosine_similarity": float(cosine_sim),
            "W_shape": W.shape,
            "alpha": alpha,
        }

    def save(self, path: Path) -> None:
        if self._W is None:
            raise ValueError("No W matrix to save.")
        np.save(path, self._W)

    def load(self, path: Path) -> None:
        self._W = np.load(path)


_aligner: Optional[CLIPAligner] = None


def get_aligner() -> CLIPAligner:
    global _aligner
    if _aligner is None:
        _aligner = CLIPAligner()
    return _aligner
