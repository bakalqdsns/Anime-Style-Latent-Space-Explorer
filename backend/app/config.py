import os
from pathlib import Path
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "Anime Visual Language Engine"
    app_version: str = "0.1.0"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/anime_engine.db"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "keyframes"

    # Redis (Phase 5)
    redis_url: str = "redis://localhost:6379/0"

    # LLM
    llm_provider: str = "deepseek"
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # ML Models
    clip_model: str = "openai/clip-vit-large-patch14"
    dinov2_model: str = "facebook/dinov2-vitl14"

    # Data paths
    data_dir: Path = Path("./data")
    data_raw_dir: Path = Path("./data/raw")
    data_frames_dir: Path = Path("./data/frames")
    data_cache_dir: Path = Path("./data/cache")
    data_output_dir: Path = Path("./data/output")
    embedding_cache_dir: Path = Path("./data/cache/embeddings")
    axis_cache_dir: Path = Path("./data/cache/axes")
    style_axes_config: Path = Path("./data/style_axes.json")

    # Clustering params
    umap_n_neighbors: int = 15
    umap_min_dist: float = 0.1
    hdbscan_min_cluster_size: int = 50
    hdbscan_min_samples: int = 10

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Resolve relative paths from PROJECT_ROOT
        project_root = Path(__file__).parent.parent.parent.resolve()
        for attr in [
            "data_dir",
            "data_raw_dir",
            "data_frames_dir",
            "data_cache_dir",
            "data_output_dir",
            "embedding_cache_dir",
            "axis_cache_dir",
            "style_axes_config",
        ]:
            val = getattr(self, attr)
            if isinstance(val, Path) and not val.is_absolute():
                setattr(self, attr, project_root / val)

        # Resolve SQLite database path to absolute
        if self.database_url.startswith("sqlite"):
            prefix = "sqlite+aiosqlite:///"
            db_path = self.database_url[len(prefix):]
            db_path_obj = Path(db_path)
            if not db_path_obj.is_absolute():
                abs_db_path = project_root / db_path
                self.database_url = prefix + str(abs_db_path.resolve())

    @property
    def qdrant_enabled(self) -> bool:
        """Check if Qdrant is configured and reachable."""
        return bool(self.qdrant_url and self.qdrant_url != "http://localhost:6333")


@lru_cache
def get_settings() -> Settings:
    return Settings()
