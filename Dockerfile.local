    FROM python:3.10-slim

    RUN apt-get update && \
    apt-get install -y --no-install-recommends --fix-missing \
        chromium-driver \
        ffmpeg \
        fonts-nanum && \
    rm -rf /var/lib/apt/lists/*
    
    WORKDIR /app
    COPY requirements.txt .
    RUN pip install --no-cache-dir -r requirements.txt
    
    COPY . .
    
    ENV GOOGLE_APPLICATION_CREDENTIALS=/app/keys/tts.json
    
    EXPOSE 8000
    CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
    