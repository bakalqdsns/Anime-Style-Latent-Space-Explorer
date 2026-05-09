#!/usr/bin/env python3
"""
Build baseline dataset from extracted keyframes.

Usage:
    python scripts/build_baseline.py ./data/frames --anime-list ./anime_list.jsonl
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.embedder import Embedder
from app.core.aligner import get_aligner
from app.core.style_axis import initialize_style_axes, project_embedding
from app.core.clusterizer import Clusterizer
from app.core.searcher import index_keyframe
from app.core.keyframe import KeyframeExtractor
from app.config import get_settings
import numpy as np


def process_anime(anime_dir: Path, settings, embedder, aligner, all_axes):
    """Process all keyframes in an anime directory."""
    # Find all extracted frame images
    frame_files = sorted(anime_dir.glob("frame_*.jpg"))
    if not frame_files:
        return 0

    print(f"  Processing {len(frame_files)} frames...")
    embeddings = embedder.embed_batch([str(f) for f in frame_files])

    projections = []
    for emb in embeddings:
        if aligner.is_trained:
            aligned = aligner.project(emb)
        else:
            # Fallback: use CLIP image encoding
            from PIL import Image
            aligned = aligner.encode_image(Image.open(frame_files[0]).convert("RGB"))
        scores = project_embedding(aligned)
        projections.append(scores)

    # Index in Qdrant
    metadata_file = anime_dir / f"{anime_dir.stem}_keyframes.json"
    metadata = {}
    if metadata_file.exists():
        with open(metadata_file) as f:
            metadata = json.load(f).get("metadata", {})

    for frame_path, emb, proj in zip(frame_files, embeddings, projections):
        payload = {
            "anime": metadata.get("anime"),
            "studio": metadata.get("studio"),
            "director": metadata.get("director"),
            "path": str(frame_path),
        }
        try:
            index_keyframe(frame_path.stem, emb, payload, dim=embedder.embedding_dim)
        except Exception as e:
            print(f"  Warning: Qdrant indexing failed: {e}")

    return len(frame_files)


def main():
    parser = argparse.ArgumentParser(description="Build baseline dataset")
    parser.add_argument("data_dir", type=Path, help="Directory containing anime subdirectories")
    parser.add_argument("--anime-list", type=Path, help="JSONL file with anime metadata")
    args = parser.parse_args()

    settings = get_settings()
    print("Initializing models...")

    # Embedder
    embedder = Embedder(
        model_name=settings.dinov2_model,
        cache_dir=settings.embedding_cache_dir,
        batch_size=32,
    )
    print(f"  DINOv2 model: {settings.dinov2_model} (dim={embedder.embedding_dim})")

    # Aligner
    aligner = get_aligner()
    if aligner.is_trained:
        print("  Aligner: W matrix loaded")
    else:
        print("  Aligner: not trained (using CLIP fallback)")

    # Style axes
    try:
        initialize_style_axes()
        all_axes = {}
        print("  Style axes: 21 axes initialized")
    except FileNotFoundError:
        print("  Style axes: not initialized (skip)")
        all_axes = None

    # Process each anime subdirectory
    anime_dirs = [d for d in args.data_dir.iterdir() if d.is_dir()]
    print(f"Found {len(anime_dirs)} anime directories")

    total_frames = 0
    for anime_dir in anime_dirs:
        print(f"\nProcessing: {anime_dir.name}")
        try:
            n = process_anime(anime_dir, settings, embedder, aligner, all_axes)
            total_frames += n
        except Exception as e:
            print(f"  Error: {e}")

    print(f"\nDone! Total frames processed: {total_frames}")


if __name__ == "__main__":
    main()
