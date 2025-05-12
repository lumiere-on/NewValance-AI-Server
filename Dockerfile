######################## 1) Builder ########################
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

# 최소 패키지
RUN apt-get update && \
    apt-get install -y --no-install-recommends python3.10 python3-pip git wget unzip && \
    rm -rf /var/lib/apt/lists/*

# 파이썬 deps + PyTorch nightly/cu124 + torchao
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        --extra-index-url https://download.pytorch.org/whl/nightly/cu124 \
        -r requirements.txt

######################## 2) Runtime (Slim) #################
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

# 런타임에 꼭 필요한 OS 패키지
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        chromium-browser chromium-driver \
        ffmpeg fonts-nanum libgl1 libgomp1 wget && \
    rm -rf /var/lib/apt/lists/*

# 파이썬 런타임 복사
COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin

# 불필요 파일 제거로 용량 ↓
RUN find /usr/local/lib/python3.10/site-packages -name "tests" -type d -exec rm -rf {} + && \
    find /usr/local/lib/python3.10/site-packages -name "*.pyi" -delete || true

# 애플리케이션 소스
WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
