# syntax=docker/dockerfile:1

# ---------- Stage 1 : builder ----------
FROM python:3.12-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /build
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
# torch + torchvision CPU-only, meme index (evite le mismatch torchvision::nms)
RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
RUN pip install --no-cache-dir -r requirements.txt
# Pre-telecharge CLIP ViT-B-32 pour un runtime 100% offline
COPY prewarm_clip.py .
RUN python prewarm_clip.py

# ---------- Stage 2 : runtime ----------
FROM python:3.12-slim AS runtime
# libgomp1 : requis par lightgbm (OpenMP) sur Debian slim
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 && rm -rf /var/lib/apt/lists/*
ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    KMP_DUPLICATE_LIB_OK=TRUE \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    MLFLOW_TRACKING_URI=sqlite:///mlflow.db \
    MIROIR_PG_HOST=host.docker.internal
WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /root/.cache/huggingface /root/.cache/huggingface
COPY api/ ./api/
COPY src/ ./src/
COPY data/synthetic/profiles.parquet data/synthetic/train.parquet ./data/synthetic/
COPY mlflow.db ./mlflow.db
COPY mlruns/ ./mlruns/
# Rend le MLflow Model Registry portable : chemins absolus macOS -> /app
COPY rewrite_mlflow_paths.py .
RUN python rewrite_mlflow_paths.py
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
