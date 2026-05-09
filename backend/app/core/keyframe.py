"""
Keyframe extraction — ffmpeg + blur detection + scene change filtering.

No TransNetV2 in MVP: uses ffmpeg scene detection + Laplacian blur filter.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import uuid
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

from app.config import get_settings


settings = get_settings()


class KeyframeExtractor:
    """
    Extract representative keyframes from a video.

    Pipeline:
    1. ffmpeg scene detection → candidate frames at scene boundaries
    2. Blur detection (Laplacian variance) → remove blurry frames
    3. Content hashing → remove near-duplicates
    """

    def __init__(
        self,
        fps: float = 1.0,
        scene_threshold: float = 0.4,
        blur_threshold: float = 100.0,
        min_interval_sec: float = 2.0,
    ):
        self.fps = fps
        self.scene_threshold = scene_threshold  # ffmpeg scene detection threshold
        self.blur_threshold = blur_threshold     # Laplacian variance threshold
        self.min_interval = min_interval_sec

    def extract(
        self,
        video_path: str | Path,
        output_dir: str | Path,
        metadata: Optional[dict] = None,
    ) -> list[dict]:
        """
        Extract keyframes from a video.

        Args:
            video_path: path to MP4 video
            output_dir: directory to save extracted frames
            metadata: dict with anime, studio, director, year

        Returns:
            list of {id, path, timestamp, width, height, hash}
        """
        video_path = Path(video_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Get scene boundaries using ffmpeg
        candidates = self._get_scene_frames(video_path)

        if not candidates:
            # Fallback: uniform sampling
            candidates = self._uniform_sample(video_path)

        # Step 2: Filter blurry frames and deduplicate
        keyframes = []
        seen_hashes = set()
        last_save_ts = -999.0

        for timestamp in sorted(candidates):
            # Enforce minimum interval
            if timestamp - last_save_ts < self.min_interval:
                continue

            frame_path = output_dir / f"frame_{uuid.uuid4().hex[:8]}.jpg"

            try:
                # Extract frame at timestamp
                success = self._extract_frame(video_path, timestamp, frame_path)
                if not success:
                    continue

                # Blur check
                blur_score = self._compute_blur(frame_path)
                if blur_score < self.blur_threshold:
                    frame_path.unlink(missing_ok=True)
                    continue

                # Hash deduplication
                frame_hash = self._content_hash(frame_path)
                if frame_hash in seen_hashes:
                    frame_path.unlink(missing_ok=True)
                    continue
                seen_hashes.add(frame_hash)

                # Get dimensions
                img = cv2.imread(str(frame_path))
                if img is None:
                    frame_path.unlink(missing_ok=True)
                    continue

                h, w = img.shape[:2]

                keyframes.append({
                    "id": str(uuid.uuid4()),
                    "path": str(frame_path),
                    "timestamp": float(timestamp),
                    "width": int(w),
                    "height": int(h),
                    "hash": frame_hash,
                    "blur_score": float(blur_score),
                })
                last_save_ts = timestamp

            except Exception:
                continue

        return keyframes

    def _get_scene_frames(self, video_path: Path) -> list[float]:
        """Use ffmpeg scene detection to find scene boundaries."""
        timestamps = []
        try:
            # ffmpeg scene detection: select frames where scene changes
            cmd = [
                "ffmpeg",
                "-i", str(video_path),
                "-filter:v", f"select='gt(scene,{self.scene_threshold})',showinfo",
                "-f", "null",
                "-",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
            # Parse pts_time from showinfo
            for line in result.stderr.split("\n"):
                if "pts_time" in line:
                    for part in line.split():
                        if part.startswith("pts_time:"):
                            ts = float(part.split(":")[1].strip())
                            timestamps.append(ts)
        except Exception:
            pass
        return timestamps

    def _uniform_sample(self, video_path: Path) -> list[float]:
        """Uniform sampling when scene detection fails."""
        cap = cv2.VideoCapture(str(video_path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / fps if fps > 0 else 0
        cap.release()

        interval = 1.0 / self.fps
        return [i * interval for i in range(int(duration * self.fps))]

    def _extract_frame(
        self,
        video_path: Path,
        timestamp: float,
        output_path: Path,
    ) -> bool:
        """Extract a single frame at the given timestamp."""
        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-ss", str(timestamp),
                "-i", str(video_path),
                "-vframes", "1",
                "-q:v", "2",
                str(output_path),
            ]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0 and output_path.exists()
        except Exception:
            return False

    def _compute_blur(self, image_path: Path) -> float:
        """Compute Laplacian variance for blur detection."""
        img = cv2.imread(str(image_path))
        if img is None:
            return 0.0
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        return float(cv2.Laplacian(gray, cv2.CV_64F).var())

    def _content_hash(self, image_path: Path) -> str:
        """Compute perceptual hash for deduplication."""
        img = cv2.imread(str(image_path))
        if img is None:
            return ""
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # Simple average hash
        resized = cv2.resize(gray, (8, 8))
        avg = resized.mean()
        bits = "".join("1" if px > avg else "0" for row in resized for px in row)
        return hex(int(bits, 2))[2:]
