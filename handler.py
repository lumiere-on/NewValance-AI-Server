# handler.py
from runpod.serverless.modules.rp_fastapi import runpod_fastapi
from app.main import app  # main.py에 정의된 FastAPI app 불러오기

handler = runpod_fastapi(app)
