from fastapi import APIRouter, BackgroundTasks
from app.core.logger import logger
from app.services import crawler

router = APIRouter(prefix="/crawl", tags=["Crawler"])


@router.get("/", summary="네이버 섹션 헤드라인 크롤링")
async def crawl(bg: BackgroundTasks):
    def _job():
        data = crawler.crawl_headlines()
        logger.info(f"[CRAWL] headlines={len(data)}")
    bg.add_task(_job)
    return {"msg": "크롤링 시작! 로그에서 진행 상황을 확인하세요."}
