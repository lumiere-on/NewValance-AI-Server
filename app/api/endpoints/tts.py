from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services import tts
from app.core.logger import logger
from pathlib import Path

class TTSIn(BaseModel):
    texts: list[str]
    style: str = "formal"   # formal / casual

router = APIRouter(prefix="/tts", tags=["TTS"])

@router.post("/", summary="TTS(MP3) 생성")
async def tts_make(body: TTSIn, bg: BackgroundTasks):
    def _job():
        for i, txt in enumerate(body.texts):
            out = tts.synthesize(txt, body.style, f"output_tts_{i}.mp3")
            logger.info(f"[TTS] saved {Path(out).name}")
    bg.add_task(_job)
    return {"msg": "TTS 작업 시작!"}
