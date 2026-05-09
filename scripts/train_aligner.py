#!/usr/bin/env python3
"""
Train the DINOv2→CLIP alignment matrix W.

Usage:
    python scripts/train_aligner.py \
        --samples ./alignment_samples.jsonl \
        --output ./data/aligner_W.npy \
        --dinov2 ./data/embeddings \
        --alpha 1.0

The samples file should contain JSONL with:
    {"image_path": "...", "text_prompt": "..."}
"""
from __future__ import annotations

import argparse
import json
import numpy as np
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.embedder import Embedder
from app.core.aligner import CLIPAligner
from app.core.keyframe import KeyframeExtractor
from app.config import get_settings


def main():
    parser = argparse.ArgumentParser(description="Train DINOv2→CLIP alignment matrix")
    parser.add_argument("--samples", type=Path, required=True, help="JSONL with image+text pairs")
    parser.add_argument("--output", type=Path, default=Path("./data/aligner_W.npy"))
    parser.add_argument("--alpha", type=float, default=1.0, help="Ridge regularization")
    args = parser.parse_args()

    settings = get_settings()

    print("Loading models...")
    embedder = Embedder(settings.dinov2_model, batch_size=32)
    aligner = CLIPAligner(clip_model_name=settings.clip_model)

    # Load samples
    X_list, Y_list = [], []
    with open(args.samples) as f:
        for line in f:
            sample = json.loads(line)
            img_path = sample["image_path"]
            text_prompt = sample["text_prompt"]

            if not Path(img_path).exists():
                print(f"  Skipping missing: {img_path}")
                continue

            # DINOv2 embedding
            dinov2_emb = embedder.embed_image(img_path)

            # CLIP text embedding
            clip_emb = aligner.encode_text(text_prompt).squeeze()

            X_list.append(dinov2_emb)
            Y_list.append(clip_emb)

    X = np.stack(X_list)
    Y = np.stack(Y_list)
    print(f"Training with {len(X)} samples")
    print(f"  X shape: {X.shape}, Y shape: {Y.shape}")

    metrics = aligner.train(X, Y, alpha=args.alpha)
    print(f"Training complete:")
    print(f"  R² score: {metrics['r2_score']:.4f}")
    print(f"  Mean cosine similarity: {metrics['mean_cosine_similarity']:.4f}")

    # Save
    args.output.parent.mkdir(parents=True, exist_ok=True)
    aligner.save(args.output)
    print(f"W matrix saved to {args.output}")


if __name__ == "__main__":
    main()
