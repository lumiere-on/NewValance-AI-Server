from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List
from app.services.moviepy import build_and_upload
from app.core.logger import logger

router = APIRouter(prefix="/merge", tags=["Merge"])

class MergeIn(BaseModel):
    video_dir: str               # output_*.mp4 폴더
    formal_subs: List[str]       # 5줄
    casual_subs: List[str]
    formal_mp3: str
    casual_mp3: str
    article_idx: str
    news_title: str              # DB 저장용
    summary_text: str            # 태그 생성용
    upload: bool = True          # S3 업로드 여부

@router.post("/", summary="MP4+MP3 병합→썸네일·태그 생성 & 업로드")
async def merge_make(body: MergeIn, bg: BackgroundTasks):
    def _job():
        urls = build_and_upload(
            video_dir   = body.video_dir,
            formal_subs = body.formal_subs,
            casual_subs = body.casual_subs,
            formal_mp3  = body.formal_mp3,
            casual_mp3  = body.casual_mp3,
            article_idx = body.article_idx,
            news_title  = body.news_title,
            summary_text= body.summary_text,
            upload      = body.upload,
        )
        logger.info(f"[MERGE] idx={body.article_idx} → {urls}")
    bg.add_task(_job)
    return {"msg": "병합·썸네일·태그 작업 시작!"}
