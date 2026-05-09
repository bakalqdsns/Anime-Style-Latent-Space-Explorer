"""
DINOv2 image embedding — ViT-L/14 (1024-dim).

Caches embeddings by content hash (pHash) to avoid recomputation.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
from typing import Optional

import imagehash
import numpy as np
import torch
import torchvision.transforms as T
from PIL import Image
from tqdm import tqdm


# Model cache — loaded lazily
_dinov2_model: Optional[torch.nn.Module] = None
_dinov2_device: Optional[torch.device] = None


def _get_device() -> torch.device:
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_dinov2(model_name: str = "facebook/dinov2-vitl14") -> torch.nn.Module:
    """Load DINOv2 model lazily."""
    global _dinov2_model, _dinov2_device
    if _dinov2_model is None:
        _dinov2_device = _get_device()
        _dinov2_model = torch.hub.load("facebookresearch/dinov2", model_name)
        _dinov2_model.to(_dinov2_device)
        _dinov2_model.eval()
    return _dinov2_model


def get_transform() -> T.Compose:
    return T.Compose([
        T.Resize(256),
        T.CenterCrop(224),
        T.ToTensor(),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])


def _compute_phash(image_path: str | Path) -> str:
    """Compute perceptual hash for cache lookup."""
    img = Image.open(image_path).convert("RGB")
    return str(imagehash.phash(img, hash_size=12))


def _embedding_cache_path(cache_dir: Path, phash: str, model_name: str) -> Path:
    safe_name = model_name.replace("/", "_")
    return cache_dir / f"{safe_name}_{phash}.npy"


class Embedder:
    """DINOv2 image embedder with hash-based caching."""

    def __init__(
        self,
        model_name: str = "facebook/dinov2-vitl14",
        cache_dir: Path | None = None,
        batch_size: int = 32,
    ):
        self.model_name = model_name
        self.cache_dir = Path(cache_dir) if cache_dir else None
        self.batch_size = batch_size
        self._transform = get_transform()

    def _load_model(self) -> torch.nn.Module:
        return load_dinov2(self.model_name)

    def embed_image(self, image_path: str | Path) -> np.ndarray:
        """Embed a single image, returns 1024-dim vector."""
        model = self._load_model()
        device = _dinov2_device or _get_device()

        if self.cache_dir:
            phash = _compute_phash(image_path)
            cache_path = _embedding_cache_path(self.cache_dir, phash, self.model_name)
            if cache_path.exists():
                return np.load(cache_path)

        img = Image.open(image_path).convert("RGB")
        tensor = self._transform(img).unsqueeze(0).to(device)

        with torch.no_grad():
            embedding = model(tensor).cpu().numpy().squeeze()

        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            np.save(cache_path, embedding)

        return embedding

    def embed_batch(self, image_paths: list[str | Path]) -> np.ndarray:
        """Embed a batch of images, returns (N, 1024) array."""
        model = self._load_model()
        device = _dinov2_device or _get_device()
        embeddings = []
        paths = [str(p) for p in image_paths]

        for i in tqdm(range(0, len(paths), self.batch_size), desc="Embedding"):
            batch_paths = paths[i : i + self.batch_size]
            tensors = []
            uncached = []

            for j, path in enumerate(batch_paths):
                if self.cache_dir:
                    phash = _compute_phash(path)
                    cache_path = _embedding_cache_path(self.cache_dir, phash, self.model_name)
                    if cache_path.exists():
                        embeddings.append(np.load(cache_path))
                        continue
                uncached.append((j, path))

            if uncached:
                for _, path in uncached:
                    img = Image.open(path).convert("RGB")
                    tensors.append(self._transform(img))

                batch = torch.stack(tensors).to(device)
                with torch.no_grad():
                    batch_emb = model(batch).cpu().numpy()

                for k, (j, path) in enumerate(uncached):
                    emb = batch_emb[k]
                    embeddings.append(emb)
                    if self.cache_dir:
                        phash = _compute_phash(path)
                        cp = _embedding_cache_path(self.cache_dir, phash, self.model_name)
                        self.cache_dir.mkdir(parents=True, exist_ok=True)
                        np.save(cp, emb)

        return np.stack(embeddings)

    def embed_pil_image(self, pil_image: Image.Image) -> np.ndarray:
        """Embed a PIL Image directly (for API uploads)."""
        model = self._load_model()
        device = _dinov2_device or _get_device()
        tensor = self._transform(pil_image).unsqueeze(0).to(device)
        with torch.no_grad():
            return model(tensor).cpu().numpy().squeeze()

    @property
    def embedding_dim(self) -> int:
        if "vitl14" in self.model_name.lower():
            return 1024
        elif "vitb14" in self.model_name.lower():
            return 768
        elif "vitg14" in self.model_name.lower():
            return 1536
        return 1024
