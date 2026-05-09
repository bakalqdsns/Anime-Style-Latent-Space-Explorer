# syntax=docker/dockerfile:1
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    ffmpeg libgl1-mesa-glx libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install DINOv2
RUN pip install --no-cache-dir \
    torch torchvision --index-url https://download.pytorch.org/whl/cu121

# Copy app
COPY app/ ./app/
COPY data/ ./data/
RUN mkdir -p data/cache/embeddings data/cache/axes data/output

# Env
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Expose
EXPOSE 8000

# Run
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
