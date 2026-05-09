"""
Initialize style axes — compute CLIP direction vectors.

Run once before using the system:
    python -m scripts.init_style_axes
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.style_axis import initialize_style_axes
from app.config import get_settings

settings = get_settings()
print("Initializing style axes...")
print(f"  CLIP model: {settings.clip_model}")
print(f"  Cache dir: {settings.axis_cache_dir}")

initialize_style_axes(force_recompute=True)
print("Done! 21 style axes initialized.")
