from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from typing import List, Optional
from app.services.pipeline import run

router = APIRouter(prefix="/pipeline", tags=["Pipeline"])

class PipeIn(BaseModel):
    sections: Optional[List[str]] = None   # ['100','101',…]  None=전체
    upload: bool = True
    limit: int = 5                        # 기사 N개만 처리

@router.post("/", summary="뉴스→쇼츠 전체 파이프라인 실행")
async def pipeline(body: PipeIn, bg: BackgroundTasks):
    bg.add_task(
        run,
        sections=body.sections,
        upload=body.upload,
        limit=body.limit,
    )
    return {
        "msg": (
            f"파이프라인 시작! sections={body.sections or 'ALL'}, "
            f"limit={body.limit}, upload={body.upload}"
        )
    }
