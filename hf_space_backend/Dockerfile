# TRINETRA / SatQuery AI — Production Container Image
# Optimized for Hugging Face Spaces (Free 16GB CPU Tier) & Cloud Run / Render / Railway
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=7860 \
    HOST=0.0.0.0

# Install system dependencies for GDAL/Rasterio, OpenCV/PIL, and PyTorch CPU
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    libgl1 \
    libglib2.0-0 \
    curl \
    git \
    git-lfs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install PyTorch CPU first to keep image lightweight and avoid unnecessary CUDA bloat (~1.5GB savings)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu

# Install remaining backend requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . /app/backend
WORKDIR /app/backend

# Create required output and upload directories with non-root UID 1000 ownership for Hugging Face Spaces
RUN useradd -m -u 1000 user && \
    mkdir -p outputs/runs outputs/export_packages uploads/workstation && \
    chown -R user:user /app && \
    chmod -R 777 /app

USER user

EXPOSE 7860

# Launch FastAPI backend with uvicorn
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-7860} --timeout-keep-alive 75"]
