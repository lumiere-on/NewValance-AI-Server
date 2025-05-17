FROM nvidia/cuda:12.1.1-devel-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6;8.9"

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 python3.10-dev python3-pip \
        build-essential gcc g++ make clang \
        fonts-nanum \
        libnss3 libx11-6 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        libatk1.0-0 libatk-bridge2.0-0 libgbm1 libasound2 libpangocairo-1.0-0 \
        libcups2 libxext6 libxfixes3 libxrender1 \
        fonts-liberation ca-certificates unzip wget gnupg && \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub | gpg --dearmor -o /usr/share/keyrings/google-linux.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN python3.10 -m pip install --upgrade pip && \
    python3.10 -m pip install --no-cache-dir -r requirements.txt && \
    rm -rf ~/.cache /root/.cache /tmp/*

WORKDIR /app
COPY . .

# 실행 스테이지 (최소한의 런타임 환경)
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

WORKDIR /app
COPY --from=builder /usr/bin/python3.10 /usr/bin/python3.10
COPY --from=builder /usr/local/bin/pip3 /usr/local/bin/pip3
COPY --from=builder /usr/local/lib/python3.10/site-packages/ /usr/local/lib/python3.10/site-packages/
COPY --from=builder /app /app

RUN ln -sf /usr/bin/python3.10 /usr/bin/python && \
    ln -sf /usr/local/bin/pip3 /usr/bin/pip && \
    apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libgl1 libgomp1 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]