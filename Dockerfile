# 수정된 Dockerfile (CUDA 12.4 기반)
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    chromium-driver \
    ffmpeg \
    fonts-nanum \
    libgl1 \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cu121

COPY . .

ENV GOOGLE_APPLICATION_CREDENTIALS=/app/keys/tts.json
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
