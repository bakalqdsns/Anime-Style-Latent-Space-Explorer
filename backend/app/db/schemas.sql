-- Anime Visual Language Engine - PostgreSQL Schema
-- Run with: psql -U postgres -d anime_engine -f schemas.sql

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Keyframes: extracted video frames
CREATE TABLE keyframes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    path VARCHAR(512) NOT NULL,
    video_name VARCHAR(256),
    anime VARCHAR(256),
    studio VARCHAR(256),
    director VARCHAR(256),
    year INTEGER,
    timestamp FLOAT,  -- seconds in original video
    width INTEGER,
    height INTEGER,
    hash VARCHAR(64),  -- content hash for deduplication
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_keyframes_anime ON keyframes(anime);
CREATE INDEX idx_keyframes_hash ON keyframes(hash);

-- Embeddings: DINOv2 feature vectors
CREATE TABLE embeddings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyframe_id UUID NOT NULL REFERENCES keyframes(id) ON DELETE CASCADE,
    model_name VARCHAR(64) NOT NULL,  -- e.g. "dinov2-vitl14"
    vector FLOAT[] NOT NULL,  -- 1024-dim for DINOv2
    dim INTEGER NOT NULL,
    mapped_vector FLOAT[],  -- 768-dim after CLIP alignment W matrix
    mapped_dim INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_embeddings_keyframe ON embeddings(keyframe_id);
CREATE INDEX idx_embeddings_model ON embeddings(model_name);

-- Style axes: predefined semantic style dimensions
CREATE TABLE style_axes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category VARCHAR(32) NOT NULL,  -- COLOR / LIGHTING / COMPOSITION / DIRECTING
    name VARCHAR(64) NOT NULL UNIQUE,
    prompt_positive TEXT NOT NULL,
    prompt_negative TEXT,
    description TEXT,
    direction_vector FLOAT[],  -- CLIP 768-dim direction vector
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_style_axes_category ON style_axes(category);
CREATE INDEX idx_style_axes_name ON style_axes(name);

-- Style projections: per-frame axis scores
CREATE TABLE style_projections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyframe_id UUID NOT NULL REFERENCES keyframes(id) ON DELETE CASCADE,
    style_axis_id UUID NOT NULL REFERENCES style_axes(id) ON DELETE CASCADE,
    score FLOAT NOT NULL,  -- [-1, 1] or [0, 1]
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(keyframe_id, style_axis_id)
);

CREATE INDEX idx_projections_keyframe ON style_projections(keyframe_id);
CREATE INDEX idx_projections_axis ON style_projections(style_axis_id);

-- Clusters: style space clusters
CREATE TABLE clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128),
    color VARCHAR(8),  -- hex color like "#FF6B6B"
    centroid FLOAT[] NOT NULL,  -- 768-dim centroid in CLIP-aligned space
    size INTEGER DEFAULT 0,
    representative_frame_id UUID REFERENCES keyframes(id),
    params_hash VARCHAR(64),  -- hash of UMAP/HDBSCAN params used
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Style space embeddings: UMAP coordinates + cluster assignment
CREATE TABLE style_space_embeddings (
    keyframe_id UUID PRIMARY KEY REFERENCES keyframes(id) ON DELETE CASCADE,
    umap_x FLOAT NOT NULL,
    umap_y FLOAT NOT NULL,
    umap_z FLOAT,
    cluster_id UUID REFERENCES clusters(id),
    params_hash VARCHAR(64),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_style_space_cluster ON style_space_embeddings(cluster_id);

-- Prompts: generated AI prompts
CREATE TABLE prompts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    keyframe_id UUID NOT NULL REFERENCES keyframes(id) ON DELETE CASCADE,
    prompt_text TEXT NOT NULL,
    style_axes_snapshot JSONB,  -- snapshot of axis scores at generation time
    llm_provider VARCHAR(32),  -- which LLM was used
    confidence FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_prompts_keyframe ON prompts(keyframe_id);

-- Jobs: async processing job tracking
CREATE TABLE jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_type VARCHAR(64) NOT NULL,  -- extract / embed / project / cluster / generate
    status VARCHAR(32) NOT NULL DEFAULT 'pending',  -- pending / running / completed / failed
    params JSONB,
    result JSONB,
    error TEXT,
    progress INTEGER DEFAULT 0,  -- 0-100
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_type ON jobs(job_type);

-- Aligner matrices: trained DINOv2→CLIP projection weights
CREATE TABLE aligner_matrices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(128) NOT NULL UNIQUE,
    matrix FLOAT[] NOT NULL,  -- flattened W matrix (768 * 1024)
    clip_model VARCHAR(64),
    dinov2_model VARCHAR(64),
    trained_samples INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
