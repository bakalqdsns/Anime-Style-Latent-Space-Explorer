#!/usr/bin/env python3
"""
Extract keyframes from anime videos.

Usage:
    python scripts/extract_keyframes.py /path/to/video.mp4 --output ./data/frames/bakemonogatari
    python scripts/extract_keyframes.py /path/to/anime_folder --output ./data/frames
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.keyframe import KeyframeExtractor
from app.config import get_settings


def extract_video(video_path: Path, output_dir: Path, metadata: dict):
    extractor = KeyframeExtractor(fps=1.0, scene_threshold=0.4, blur_threshold=80)
    keyframes = extractor.extract(video_path, output_dir, metadata)

    print(f"Extracted {len(keyframes)} keyframes from {video_path.name}")
    for kf in keyframes:
        print(f"  {kf['timestamp']:.1f}s → {Path(kf['path']).name} (blur={kf['blur_score']:.0f})")

    # Save metadata
    meta_out = output_dir / f"{video_path.stem}_keyframes.json"
    with open(meta_out, "w", encoding="utf-8") as f:
        json.dump({"video": str(video_path), "keyframes": keyframes, "metadata": metadata}, f, indent=2)
    print(f"Metadata saved to {meta_out}")
    return keyframes


def main():
    parser = argparse.ArgumentParser(description="Extract keyframes from anime videos")
    parser.add_argument("input", type=Path, help="Video file or folder of videos")
    parser.add_argument("--output", "-o", type=Path, default=Path("./data/frames"))
    parser.add_argument("--fps", type=float, default=1.0)
    parser.add_argument("--scene-threshold", type=float, default=0.4)
    parser.add_argument("--blur-threshold", type=float, default=80.0)
    parser.add_argument("--anime", type=str, help="Anime title")
    parser.add_argument("--studio", type=str, help="Studio name")
    parser.add_argument("--director", type=str, help="Director name")
    parser.add_argument("--year", type=int, help="Release year")

    args = parser.parse_args()

    settings = get_settings()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    metadata = {
        "anime": args.anime,
        "studio": args.studio,
        "director": args.director,
        "year": args.year,
    }

    if args.input.is_file():
        videos = [args.input]
    elif args.input.is_dir():
        videos = list(args.input.glob("*.mp4")) + list(args.input.glob("*.mkv"))
    else:
        print(f"Error: {args.input} not found")
        sys.exit(1)

    for video in videos:
        print(f"\nProcessing: {video}")
        anime_dir = output_dir / (args.anime or video.stem)
        anime_dir.mkdir(parents=True, exist_ok=True)
        try:
            extract_video(video, anime_dir, metadata)
        except Exception as e:
            print(f"Error processing {video}: {e}")


if __name__ == "__main__":
    main()
