FROM --platform=linux/amd64 nvidia/cuda:12.4.0-runtime-ubuntu22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 python3-pip git wget unzip && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -U pip && \
    pip install --no-cache-dir \
        --pre torch torchvision torchaudio \
        --extra-index-url https://download.pytorch.org/whl/nightly/cu124 && \
    pip install --no-cache-dir -r requirements.txt

FROM --platform=linux/amd64 nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility

    RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3.10 python3-pip \
        ffmpeg fonts-nanum libgl1 libgomp1 \
        libnss3 libx11-6 libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 \
        libatk1.0-0 libatk-bridge2.0-0 libgbm1 libasound2 libpangocairo-1.0-0 \
        libcups2 fonts-liberation wget gnupg ca-certificates unzip && \
    wget -qO- https://dl.google.com/linux/linux_signing_key.pub \
        | gpg --dearmor -o /usr/share/keyrings/google-linux.gpg && \
    echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-linux.gpg] \
        http://dl.google.com/linux/chrome/deb/ stable main" \
        > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-chrome-stable && \
    CHROME_MAJOR=$(google-chrome --version | cut -d ' ' -f3 | cut -d '.' -f1) && \
    wget -q https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_MAJOR} -O /tmp/LATEST && \
    CHROMEDRIVER_VER=$(cat /tmp/LATEST) && \
    wget -q https://chromedriver.storage.googleapis.com/${CHROMEDRIVER_VER}/chromedriver_linux64.zip -O /tmp/chromedriver.zip && \
    unzip /tmp/chromedriver.zip -d /usr/local/bin && \
    chmod +x /usr/local/bin/chromedriver && \
    rm /tmp/chromedriver.zip /tmp/LATEST && \
    rm -rf /var/lib/apt/lists/*


COPY --from=builder /usr/local/lib/python3.10 /usr/local/lib/python3.10
COPY --from=builder /usr/local/bin /usr/local/bin
RUN ln -sf /usr/bin/python3.10 /usr/bin/python3

RUN find /usr/local/lib/python3.10/site-packages -name "tests" -type d -exec rm -rf {} + && \
    find /usr/local/lib/python3.10/site-packages -name "*.pyi" -delete || true

WORKDIR /app
COPY . .

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
