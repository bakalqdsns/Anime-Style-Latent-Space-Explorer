# Anime Visual Language Engine

> 动漫视觉风格空间分析与 Prompt 反推平台

## 项目概述

将动漫视觉风格建模为连续语义空间，通过风格轴系统实现:
- **风格空间可视化** — UMAP + HDBSCAN 聚类，Three.js 3D 交互地图
- **风格轴分析** — 21 个预定义语义风格轴 (色彩/光影/构图/演出)
- **Prompt 反推** — 从视觉特征自动生成 AI 图像生成 Prompt

## 技术栈

| 层级 | 技术 |
|------|------|
| 图像 Embedding | DINOv2 ViT-L/14 (1024D) |
| 语义对齐 | CLIP ViT-L/14 + 线性映射 |
| 聚类 | UMAP (768D→3D) + HDBSCAN |
| 向量检索 | Qdrant |
| 后端 | FastAPI + Pydantic |
| 前端 | React + Vite + Three.js + Tailwind |
| LLM | DeepSeek-V4-Flash (Prompt 生成) |

## 快速开始

### 环境要求

- Python 3.10+
- NVIDIA GPU (8GB+ VRAM) — DINOv2 推理用
- Node.js 18+
- PostgreSQL 15+ (可选, 也可用 SQLite 开发)
- Qdrant (可选, 也可用纯内存模式开发)

### 后端安装

```bash
# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 安装依赖
pip install -e ".[gpu]"

# 或仅 CPU 模式
pip install -e .

# 复制环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 初始化数据库
alembic upgrade head  # 如果使用 alembic
# 或直接运行: python -m app.db.init_db

# 启动后端
uvicorn app.main:app --reload --port 8000
```

### 前端安装

```bash
cd frontend
npm install
npm run dev
```

### 使用 Docker (推荐)

```bash
docker-compose up --build
```

## 开发路线

### Phase 1 — 截图 Embedding
上传图片 → DINOv2 embedding → Qdrant 相似搜索

### Phase 2 — 风格轴系统
DINOv2 + CLIP 对齐 → 21 个风格轴评分 → 雷达图可视化

### Phase 3 — 风格空间地图
UMAP + HDBSCAN → Three.js 3D 交互地图

### Phase 4 — Prompt 反推
DeepSeek-V4-Flash 生成自然语言 Prompt

### Phase 5 — 视频镜头分析
视频上传 → 批量关键帧提取 → Celery 异步处理

## 项目结构

```
anime-visual-language-engine/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── config.py            # Settings
│   │   ├── api/                # API routes
│   │   ├── core/               # AI/ML modules
│   │   ├── db/                 # Database layer
│   │   ├── vector/             # Qdrant wrapper
│   │   ├── worker/             # Celery tasks (Phase 5)
│   │   └── models/             # Pydantic models
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/              # Dashboard, Analyze, StyleMap, PromptLab
│   │   ├── components/          # Three.js, charts, upload
│   │   ├── api/                # API client
│   │   └── types/               # TypeScript interfaces
│   └── package.json
├── scripts/                     # Standalone processing scripts
├── data/                        # Data directory
├── pyproject.toml
└── .env.example
```

## 风格轴系统

### 色彩轴 (COLOR)
warm, cold, neon, pastel, low_saturation

### 光影轴 (LIGHTING)
cinematic_light, soft_light, hard_shadow, rim_light, film_grain

### 构图轴 (COMPOSITION)
negative_space, dutch_angle, centered, wide_shot, close_up

### 演出轴 (DIRECTING)
experimental, cinematic, melancholic, surreal, energetic, shaft_like

## API 文档

启动后端后访问: http://localhost:8000/docs

## License

MIT
