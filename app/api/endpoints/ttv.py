from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from app.services import ttv
from app.core.logger import logger
from pathlib import Path

class TTVIn(BaseModel):
    prompts: list[str]

router = APIRouter(prefix="/ttv", tags=["TTV"])

@router.post("/", summary="텍스트→비디오 생성")
async def ttv_make(body: TTVIn, bg: BackgroundTasks):
    def _job():
        paths = ttv.generate(body.prompts)
        logger.info(f"[TTV] generated {len(paths)} mp4 files: {[Path(p).name for p in paths]}")
    bg.add_task(_job)
    return {"msg": "TTV 작업 시작!"}
