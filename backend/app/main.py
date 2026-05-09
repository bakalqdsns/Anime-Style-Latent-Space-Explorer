"""
Anime Visual Language Engine — FastAPI Application Entry Point.
"""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db.database import init_db, close_db
from app.api import analyze, style, search, frames, prompt, embeddings


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    await init_db()
    # Ensure data directories exist
    for d in [
        settings.data_dir,
        settings.data_frames_dir,
        settings.data_cache_dir,
        settings.embedding_cache_dir,
        settings.axis_cache_dir,
    ]:
        Path(d).mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Anime Visual Style Space Analysis — DINOv2 + CLIP + UMAP",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount static files (for serving keyframe images)
    frames_dir = settings.data_frames_dir
    if frames_dir.exists():
        app.mount("/frames", StaticFiles(directory=str(frames_dir)), name="frames")

    # API routers
    app.include_router(analyze.router)
    app.include_router(style.router)
    app.include_router(search.router)
    app.include_router(frames.router)
    app.include_router(prompt.router)
    app.include_router(embeddings.router)

    @app.get("/", tags=["root"])
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    @app.get("/health", tags=["health"])
    async def health():
        return {"status": "healthy"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
